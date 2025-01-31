import logging
import os
import requests
import threading
import time

from collections import deque
from flask import Flask, request, jsonify, render_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_QUEUE_LEN = 100
DETECTION_SERVICE_URL = os.getenv("DETECTION_SERVICE_URL", "http://anomaly_detection_container:5001/health_check")


anomaly_queue = deque()
input_data_queue = deque()
output_data_queue = deque()
anomaly_lock = threading.Lock()
input_data_lock = threading.Lock()
output_data_lock = threading.Lock()

def secure_append_data(queue, data, queue_lock):
    with queue_lock:
        if len(queue)  >= MAX_QUEUE_LEN:
            queue.popleft()
            logger.warning("Max queue len - deleting the oldest entry.")
        queue.append(data)

def secure_read_data(queue, queue_lock):
    with queue_lock:
        if queue:
            return queue.popleft()
        return None

def sort_data():
    logger.info("Sorting started")
    while True:
        try:
            input_data = secure_read_data(input_data_queue, input_data_lock)
            logger.info(f"data to be sorted: {input_data}")
            if input_data:
                if input_data['result']['is_anomaly']:
                    secure_append_data(anomaly_queue, input_data, anomaly_lock)
                secure_append_data(output_data_queue, input_data, output_data_lock)
            else:
                time.sleep(1.0)
        except Exception as e:
            logger.error(f"Error sorting data: {e}")


dashboard_app = Flask(__name__)

@dashboard_app.route("/receive_data", methods=["POST"])
def receive_data():
    try:
        input_data = request.json
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400

        secure_append_data(input_data_queue, input_data, input_data_lock)
        logger.info(f"Received and queued input data: {input_data}")
        return jsonify({"message": "Data received successfully"}), 200
    
    except Exception as e:
        logger.error(f"No input data: {e}")
        return jsonify({"error": "Internal server error"}), 500

@dashboard_app.route("/")
def index():
    logger.info("dashboard rendered")
    return render_template("dashboard.html")

@dashboard_app.route("/get_latest_data", methods=["GET"])
def get_latest_data():
    logger.info("data requested")
    try:
        new_output_data = secure_read_data(output_data_queue, output_data_lock)
        new_anomaly_data = secure_read_data(anomaly_queue, anomaly_lock)
        logger.info(f"data to be sent: general: {new_output_data} & anomaly: {new_anomaly_data}")
        if new_output_data:
            return jsonify({
                "output_data": new_output_data,
                "anomaly_data": new_anomaly_data
            }), 200
        else:
            time.sleep(1.0)            
            return jsonify({
                "output_data": None,
                "anomaly_data": None
            }), 200

    except Exception as e:
        logger.error(f"Error retrieving latest data: {e}")
        return jsonify({"error": "Internal server error"}), 500


@dashboard_app.route("/check_health", methods=["GET"])
def check_health():
    """Endpoint to call the anomaly detection health check and return the result."""
    try:
        response = requests.post(DETECTION_SERVICE_URL, timeout=5)
        response_data = response.json()
        return jsonify(response_data), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Health check request failed: {e}")
        return jsonify({"status": "fail", "message": "Unable to reach anomaly detection service."}), 500


def start_background_thread():
    logger.info("Starting sorting thread...")
    thread = threading.Thread(target=sort_data, daemon=True)
    thread.start()

with dashboard_app.app_context():
    start_background_thread()

if __name__ == "__main__":
    logger.info("Dashboard started")
    dashboard_app.run(host="0.0.0.0", port=5002)