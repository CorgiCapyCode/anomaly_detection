import joblib
import logging
import numpy as np
import os
import pandas as pd
import requests
import threading
import time

from collections import deque
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# To run locally, without container.
#MODEL_PATH = "src/production/anomaly_detection/ocsvm_model.pkl"
# To run in a docker container.
MODEL_PATH = "ocsvm_model.pkl"
DASHBOARD_SERVICE_URL = os.getenv("DASHBOARD_SERVICE_URL", "http://dashboard_container:5002/dashboard")

MAX_QUEUE_LEN = 1000

def load_model(path:str):
    try:
        model = joblib.load(path)
        logger.info("Model loaded successfully.")
        return model
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return None

ocsvm_model = load_model(MODEL_PATH)


input_data_queue = deque()
output_data_queue = deque()
temp_data = pd.DataFrame(columns=["timestamp"] + list(ocsvm_model.feature_names_in_) + ["is_anomaly"])

input_data_lock = threading.Lock()
output_data_lock = threading.Lock()
temp_data_lock = threading.Lock()

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

def secure_append_left_data(queue, data, queue_lock):
    with queue_lock:
        if len(queue)  >= MAX_QUEUE_LEN:
            queue.popleft()
            logger.warning("Max queue len - deleting the oldest entry.")
        queue.appendleft(data)


def anomaly_detection():
    expected_features = ocsvm_model.feature_names_in_

    while True:
        try:
            input_data = secure_read_data(input_data_queue, input_data_lock)
            if input_data:
                missing_features = [feature for feature in expected_features if feature not in input_data]
                if missing_features:
                    logger.error(f"Data does not fit the model.")
                    break
                
                data_array = np.array([[input_data[feature] for feature in expected_features]])
                data_df = pd.DataFrame(data_array, columns=expected_features)
                
                prediction = ocsvm_model.predict(data_df)
                is_anomaly = bool(prediction[0] == -1)
                
                result = {
                    "is_anomaly": is_anomaly,
                    "details": "Anomaly detected" if is_anomaly else "Normal behavior"
                }
                
                output_data = {
                    "data": input_data,
                    "result": result
                }
                secure_append_data(output_data_queue, output_data, output_data_lock)
                
                with temp_data_lock:
                    global temp_data
                    new_entry = pd.DataFrame([{**{feat: input_data[feat] for feat in expected_features}, 
                                               "timestamp": input_data["timestamp"],
                                               "is_anomaly": is_anomaly}])
                    temp_data = pd.concat([temp_data, new_entry], ignore_index=True)
                    if len(temp_data) > 1000:
                        temp_data = temp_data.iloc[-1000:]
            else:
                time.sleep(1.0)

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")


anomaly_detection_app = Flask(__name__)


@anomaly_detection_app.route("/detection_service", methods=["POST"])
def detection_service():
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

        
def send_data_to_dashboard():
    while True:
        transfer_data = secure_read_data(output_data_queue, output_data_lock)
        if transfer_data:
            try:
                dashboard_response = requests.post(DASHBOARD_SERVICE_URL, json=transfer_data)
                if dashboard_response.status_code == 200:
                    logger.info("Data successfully sent to dashboard.")
                else:
                    logger.error(f"Failed to forward data. Error: {dashboard_response.status_code}")
                    secure_append_left_data(output_data_queue, transfer_data, output_data_lock)
            except Exception as e:
                logger.error(f"Error sending data to the dashboard: {e}")
        else:
            time.sleep(1.0)


@anomaly_detection_app.route("/health_check", methods=["POST"])
def check_model_health():
    try:
        if ocsvm_model is None:
            logger.error("Model is not loaded correctly.")
            return jsonify({"status": "fail", "message": "Model is not loaded."}), 500
    
        if temp_data.empty:
            logger.warning("Temp data is empty. No recent data processed.")
            return jsonify({"status": "warning", "message": "No recent data processed."}), 200
        
        input_queue_size = len(input_data_queue)
        output_queue_size = len(output_data_queue)
        logger.info(f"Input queue size: {input_queue_size}, Output queue size: {output_queue_size}")
        if input_queue_size > 900:
            if output_queue_size > 900:
                return jsonify({"status": "warning", "message": "Input and output data queues are almost full."}), 200
            else:
                return jsonify({"status": "warning", "message": "Input queue is almost full."}), 200
        elif output_queue_size > 900:
            return jsonify({"status": "warning", "message": "Output queue is almost full."}), 200
        else:
            return jsonify({"status": "warning", "message": "System works fine."}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "fail", "message": str(e)}), 500    


def start_anomaly_detection():
    logger.info("Starting anomaly detection process...")
    anomaly_detection()
            

if __name__ == "__main__":
    detection_thread = threading.Thread(target=start_anomaly_detection)
    detection_thread.daemon = True
    detection_thread.start()    
    
    send_data_thread = threading.Thread(target=send_data_to_dashboard)
    send_data_thread.daemon = True
    send_data_thread.start()
    
    anomaly_detection_app.run(host="0.0.0.0", port=5001)
    
    