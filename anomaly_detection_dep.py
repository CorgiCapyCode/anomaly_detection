import joblib
import logging
import numpy as np
import os
import pandas as pd
import requests
import time

from collections import deque
from flask import Flask, jsonify, request
from threading import Thread

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# To run locally, without container.
#MODEL_PATH = "src/production/anomaly_detection/ocsvm_model.pkl"
# To run in a docker container.
MODEL_PATH = "ocsvm_model.pkl"
DASHBOARD_SERVICE_URL = os.getenv("DASHBOARD_SERVICE_URL", "http://dashboard_container:5002/dashboard")

data_queue = deque()

def load_model(path: str):
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
    except FileNotFoundError:
        logger.error(f"Model file not found at {path}.")
    except Exception as e:
        logger.error(f"Error loading model: {e}")
    return None

ocsvm_model = load_model(MODEL_PATH)

anomaly_detection_app = Flask(__name__)

@anomaly_detection_app.route("/detection_service", methods=["POST"])
def detection_service():
    try:
        input_data = request.json
        if not input_data:
            return jsonify({"error": "No input data provided"}), 400
        
        expected_features = ocsvm_model.feature_names_in_
        missing_features = [feat for feat in expected_features if feat not in input_data]
        if missing_features:
            return jsonify({"error": f"Missing features: {missing_features}"}), 400
               
        data_array = np.array([[input_data[feat] for feat in expected_features]])
        data_df = pd.DataFrame(data_array, columns=expected_features)
               
        prediction = ocsvm_model.predict(data_df)
        is_anomaly = bool(prediction[0] == -1)
        
        result = {
            "is_anomaly": is_anomaly,
            "details": "Anomaly detected" if is_anomaly else "Normal behavior"
        }
        
        data_queue.append({"data": input_data, "result": result})
        
        return jsonify(result), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@anomaly_detection_app.route("/send_to_dashboard", methods=["GET"])
def send_to_dashboard_manu():
    try:
        if data_queue.empty():
            return jsonify({"message": "No values available"}), 200
        
        data_point = data_queue.popleft()
        dashboard_response = requests.post(DASHBOARD_SERVICE_URL, json=data_point)
        
        if dashboard_response.status_code == 200:
            return jsonify({"message": "Data successfully forwarded.", "data": {data_point}}), 200
        
        else:
            return jsonify({"error": f"Dashboard Service Error: {dashboard_response.status_code}, {dashboard_response.text}"}), 500
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def send_to_dashboard_auto():
    while True:
        if data_queue:
            data_point = data_queue.popleft()
            dashboard_response = requests.post(DASHBOARD_SERVICE_URL, json=data_point)
            time.sleep(0.75)
            
            if dashboard_response.status_code == 200:
                logger.info("Data successfully sent to Dashboard.")
            else:
                logger.error(f"Failed to forward data. Error: {dashboard_response.status_code}. Re-adding to the front of the queue.")
                data_queue.appendleft(data_point)
            
        else:
            time.sleep(0.9)


if __name__ == "__main__":
    thread = Thread(target=send_to_dashboard_auto)
    thread.start()    
    anomaly_detection_app.run(host="0.0.0.0", port=5001)