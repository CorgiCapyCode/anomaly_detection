import logging
from flask import Flask, jsonify, request, render_template
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_LEN_QUEUE = 10
anomalies = deque(maxlen=MAX_LEN_QUEUE)
received_data = deque(maxlen=MAX_LEN_QUEUE)

dashboard_app = Flask(__name__)
dashboard_app.config["SECRET_KEY"] = "test_application"


@dashboard_app.route("/receive_data", methods=["POST"])
def receive_data():
    try:
        input_data = request.json
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400
        
        logger.info(f"Received data: {input_data}")
        
        if input_data['result']['is_anomaly']:
            anomalies.append(input_data)
        
        received_data.append(input_data)

        return jsonify({"message": "Data received successfully"}), 200
    
    except Exception as e:
        logger.error(f"Error receiving data: {str(e)}")
        return jsonify({"error": str(e)}), 500


@dashboard_app.route("/")
def index():
    return render_template("dashboard.html")

@dashboard_app.route("/latest_data", methods=["GET"])
def latest_data():
    """
    Endpoint to fetch the latest data for the dashboard.
    """
    try:
        latest_data = []
        while len(latest_data) < MAX_LEN_QUEUE and received_data:
            latest_data.append(received_data.popleft())
        
        logger.info(f"Sent data to the dashboard: {latest_data}")
        return jsonify({
            "received_data": latest_data,
            "anomalies": list(anomalies),
        })
    
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    
if __name__ == "__main__":
    dashboard_app.run(host="0.0.0.0", port=5002)
