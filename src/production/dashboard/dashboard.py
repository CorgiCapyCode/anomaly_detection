import logging
import os
import requests
import threading
import time

from collections import deque
from datetime import datetime
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
    """
    Locks the thread while appending data to the queue. Ensures that the queue does not exceed the maximum length.
    
    Args:
        queue (deque): Queue (buffer) where the data is appended.
        data: The data to be appended to the queue.
        queue_lock (threading.Lock): Locking the thread to ensure that the data is not corrupted by other threads.
    """
    with queue_lock:
        if len(queue)  >= MAX_QUEUE_LEN:
            queue.popleft()
            logger.warning("Max queue len - deleting the oldest entry.")
        queue.append(data)

def secure_read_data(queue, queue_lock):
    """
    Locks the thread while reading data from the queue. Removes the read data.
    
    Args:
        queue (deque): Queue which serves as the source.
        queue_lock (threading.Lock): Locking the thread to ensure that the data is not corrupted by other threads.
    """
    with queue_lock:
        if queue:
            return queue.popleft()
        return None

def sort_data():
    """
    Checks the incoming data for being anomalies and appends the data to the correct queues.
    """
    logger.info("Sorting started")
    while True:
        try:
            #logger.info(f"Sorting - Data Input queue: {len(input_data_queue)}")
            input_data = secure_read_data(input_data_queue, input_data_lock)
            if input_data:
                if input_data['result']['is_anomaly']:
                    secure_append_data(anomaly_queue, input_data, anomaly_lock)
                secure_append_data(output_data_queue, input_data, output_data_lock)
                #logger.info("Data sorted successfully.")
            else:
                #logger.info("Sorting - Waiting - Empty queue.")
                time.sleep(1.0)
        except Exception as e:
            logger.error(f"Error sorting data: {e}")


dashboard_app = Flask(__name__)

@dashboard_app.route("/receive_data", methods=["POST"])
def receive_data():
    """
    Takes the output of the anomaly detection and appends it to the input queue.
    """
    try:
        #logger.info(f"AD - Data requested at: {datetime.now()}")
        input_data = request.json
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400

        secure_append_data(input_data_queue, input_data, input_data_lock)
        #logger.info(f"AD - Data appended to input data at: {datetime.now()}")
        return jsonify({"message": "Data received successfully"}), 200
    
    except Exception as e:
        logger.error(f"No input data: {e}")
        return jsonify({"error": "Internal server error"}), 500

@dashboard_app.route("/")
def index():
    """
    Generates the overall layout of the dashboard.
    """
    logger.info("dashboard rendered")
    return render_template("dashboard.html")

@dashboard_app.route("/get_latest_data", methods=["GET"])
def get_latest_data():
    """
    Loads the data to the dashboard.
    """
    #logger.info(f"Dashboard - Data requested at {datetime.now()}")
    #logger.info(f"Dashboard - Output queue size {len(output_data_queue)}")
    try:
        new_output_data = secure_read_data(output_data_queue, output_data_lock)
        new_anomaly_data = secure_read_data(anomaly_queue, anomaly_lock)
        #logger.info(f"Dashboard - Data loaded from queue at {datetime.now()}")
        #logger.info(f"Dashboard - Data Output Queue size {len(output_data_queue)}")
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
    """
    Endpoint to call the anomaly detection health check and return the result.
    """
    try:
        response = requests.post(DETECTION_SERVICE_URL, timeout=5)
        response_data = response.json()
        return jsonify(response_data), response.status_code
    except requests.exceptions.RequestException as e:
        logger.error(f"Health check request failed: {e}")
        return jsonify({"status": "fail", "message": "Unable to reach anomaly detection service."}), 500


def start_background_thread():
    """
    Starts the sorting process.
    """
    logger.info("Starting sorting thread...")
    thread = threading.Thread(target=sort_data, daemon=True)
    thread.start()

with dashboard_app.app_context():
    start_background_thread()

if __name__ == "__main__":
    logger.info("Dashboard started")
    dashboard_app.run(host="0.0.0.0", port=5002)