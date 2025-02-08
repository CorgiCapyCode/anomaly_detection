import joblib
import logging
import numpy as np
import os
import pandas as pd
import requests
import threading
import time

from collections import deque
from datetime import datetime
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# To run locally, without container.
#MODEL_PATH = "src/production/anomaly_detection/ocsvm_model.pkl"
# To run in a docker container.
MODEL_PATH = "ocsvm_model.pkl"
DASHBOARD_SERVICE_URL = os.getenv("DASHBOARD_SERVICE_URL", "http://dashboard_container:5002/dashboard")

MAX_QUEUE_LEN = 1000
temp = 10.0              # Modify for sensitivity of prediction score

def load_model(path:str):
    """
    Load the model data.
    Args:
        path (str): The path to the model data (PKL).
    
    Returns:
        model: The loaded model.
    """
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

def secure_append_left_data(queue, data, queue_lock):
    """
    Locks the thread while appending data to the queue on the left side. Ensures that the queue does not exceed the maximum length.
    
    Args:
        queue (deque): Queue (buffer) where the data is appended.
        data: The data to be appended to the queue.
        queue_lock (threading.Lock): Locking the thread to ensure that the data is not corrupted by other threads.
    """
    with queue_lock:
        if len(queue)  >= MAX_QUEUE_LEN:
            queue.popleft()
            logger.warning("Max queue len - deleting the oldest entry.")
        queue.appendleft(data)


def normalize_scores(score, temp=10.0):
    """ 
    Used to normalize the score (distance to margin) in order to create a class membership probability.
    
    Args:
        score: The distance to the margin to be normalized.
        temp: Used as a factor for normalizing. Higher values lead to "more mixed probabilities".
        
    Return:
        New score that equals a probability.
    """
    if temp <= 0:
        temp = 10.0
        logger.warning("Temp set too low, changed to standard value of 10.")
    return 1 / (1 + np.exp(-score / temp))


def calc_sensor_data_time(data: pd.DataFrame):
    """
    Calculates the time delta between the generated data stored in the temp-data storage.
    Used for health check.
    Args:
        data (pd.DataFrame): Dataset with timestamp.
    Returns:
        avg_time: Average time between the generated data.
    """
    sorted_data = data.sort_values(by="timestamp")
    time_differences = sorted_data["timestamp"].diff().dropna()
    
    avg_time = time_differences.mean().total_seconds()
    return avg_time

def calc_anomaly_ratio(data: pd.DataFrame):
    """
    Calculates the anomaly ratio.
    Used for health check.
    Args:
        data (pd.DataFrame): Dataset with timestamp.
    Return:
        anomaly_ratio: The anomaly ration in the data.        
    """
    anomaly_count = data["is_anomaly"].sum()
    total_count = len(data)
    anomaly_ratio = (anomaly_count/total_count) * 100
    return anomaly_ratio

def anomaly_detection():
    """
    Runs the anomaly detection algorithm and appends the data to the buffers.
    """
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
                
                decision_score = ocsvm_model.decision_function(data_df)[0]
                probability = normalize_scores(decision_score)
                prediction = ocsvm_model.predict(data_df)
                is_anomaly = bool(prediction[0] == -1)
                
                result = {
                    "is_anomaly": is_anomaly,
                    "anomaly_probability" : probability,
                    "details": "Anomaly detected" if is_anomaly else "Normal behavior"
                }
                
                output_data = {
                    "data": input_data,
                    "result": result,
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
    """
    Endpoint which starts the anomaly detection.
    """
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
    """
    Sends the data from the buffer to the dashboard regularly.    
    """
    while True:
        logger.info(f"Transfer - triggered at {datetime.now()} - data queue len: {len(output_data_queue)}")
        transfer_data = secure_read_data(output_data_queue, output_data_lock)
        if transfer_data:
            try:
                dashboard_response = requests.post(DASHBOARD_SERVICE_URL, json=transfer_data)
                if dashboard_response.status_code == 200:
                    logger.info(f"Transfer - Data sent at {datetime.now()}")
                else:
                    logger.error(f"Failed to forward data. Error: {dashboard_response.status_code}")
                    secure_append_left_data(output_data_queue, transfer_data, output_data_lock)
            except Exception as e:
                logger.error(f"Error sending data to the dashboard: {e}")
        else:
            logger.info("Transfer - No queued data.")
            time.sleep(1.0)


@anomaly_detection_app.route("/health_check", methods=["POST"])
def check_model_health():
    """
    Used to check the model health (some parameters).
    """
    logger.info("Triggered health check")
    base_data = temp_data
    try:
        if ocsvm_model is None:
            logger.error("Model is not loaded correctly.")
            return jsonify({"status": "fail", "message": "Model is not loaded."}), 500
    
        input_queue_size = len(input_data_queue)
        output_queue_size = len(output_data_queue)
        logger.info(f"Input queue size: {input_queue_size}, Output queue size: {output_queue_size}")
        
        if input_queue_size > 1000:
            input_queue_status = "Warning - Queue full."
        elif input_queue_size > 900:
            input_queue_status = "Warning - Queue almost full."
        else:
            input_queue_status = "Queue size is healthy."
        
        if output_queue_size > 1000:
            output_queue_status = "Warning - Queue full."
        elif output_queue_size > 900:
            output_queue_status = "Warning - Queue almost full."
        else:
            output_queue_status = "Queue size is healthy."
        avg_time = 0
        anomaly_ratio = 0
        
        logger.info(f"type base data: {type(base_data)}")

        base_data['timestamp'] = pd.to_datetime(base_data['timestamp'], errors='coerce')
        base_data['temperature'] = pd.to_numeric(base_data['temperature'], errors='coerce')
        base_data['humidity'] = pd.to_numeric(base_data['humidity'], errors='coerce')
        base_data['noise_level'] = pd.to_numeric(base_data['noise_level'], errors='coerce')

        if not base_data.empty:
            logger.info(f"Base data not empty and of type: {type(base_data)}")
            avg_time = calc_sensor_data_time(base_data)
            anomaly_ratio = calc_anomaly_ratio(base_data)
        else:
            logger.warning("Base data is empty. Skipping calculation for avg_time and anomaly_ratio.")
        
        health_status = {
            "status" : "Anomaly detection is running.",
            "input_queue_size" : input_queue_size,
            "input_queue_status" : input_queue_status,
            "output_queue_size": output_queue_size,
            "output_queue_status" : output_queue_status,
            "avg_time" : avg_time,
            "anomaly_ratio" : anomaly_ratio
        }
        logger.info(health_status)
        return jsonify(health_status), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "fail", "message": str(e)}), 500    


def start_anomaly_detection():
    """
    Starts the anomaly detection.
    """
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
    
    