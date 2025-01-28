import json
import logging
import numpy as np
import os
import random
import requests
import signal
import time

from datetime import datetime
from flask import Flask, jsonify, request
from threading import Thread, Event

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use this to run it locally from the project directory:
#FEATURES_CONFIG_PATH = "src/production/stream_data/features_config.json"

# Use this to build a container.
FEATURES_CONFIG_PATH = "features_config.json"

DETECTION_SERVICE_URL = os.getenv("DETECTION_SERVICE_URL", "http://anomaly_detection_container:5001/anomaly_detection")
MAX_RETRIES = 5
INITIAL_WAIT_TIME = 2
WAIT_TIME_MULTIPLIER = 2

# Set duration = 0 for infinite mode
duration = 600 #seconds
# Time between the data is generated.
interval = 1 #seconds

streaming_status = False
stop_streaming = Event()

def graceful_shutdown(signal, frame):
    logger.info("Gracefully shutting down the streaming service.")
    stop_streaming.set()
    
signal.signal(signal.SIGINT, graceful_shutdown)


def load_features_config(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def generate_sensor_value(distribution: str, params, sample_size: int =1):

    if distribution == "normal":
        return np.random.normal(params["mean"], params["std"], sample_size)
    elif distribution == "uniform":
        return np.random.uniform(params["low"], params["high"], sample_size)
    elif distribution == "exponential":
        return np.random.exponential(params["scale"], sample_size)
    elif distribution == "poisson":
        return np.random.poisson(params["lam"], sample_size)
    elif distribution == "lognormal":
        return np.random.lognormal(params["mean"], params["sigma"], sample_size)
    elif distribution == "gamma":
        return np.random.gamma(params["shape"], params["scale"], sample_size)
    elif distribution == "beta":
        return np.random.beta(params["a"], params["b"], sample_size)
    elif distribution == "weibull":
        return np.random.weibull(params["a"], sample_size)
    elif distribution == "triangular":
        return np.random.triangular(params["left"], params["mode"], params["right"], sample_size)
    elif distribution == "chisquare":
        return np.random.chisquare(params["df"], sample_size)
    else:
        raise ValueError(f"Distribution not supported: {distribution}")


def generate_data(features_config):

    data_point = {"timestamp": datetime.now().isoformat()}

    for feature in features_config.values():
        feature_name = feature["name"]
        distribution = feature["distribution"]
        params = feature["params"]
        anomaly_ratio = feature.get("anomaly_ratio")
        anomaly_range = feature["anomaly_range"]

        if random.random() < anomaly_ratio:
            value = random.uniform(*anomaly_range)
        else:

            value = generate_sensor_value(
                distribution=distribution,
                params=params,
                sample_size=1
            )[0]

        data_point[feature_name] = value

    return data_point


def stream_data():
    
    features_config = load_features_config(FEATURES_CONFIG_PATH)
    
    if duration == 0:
        logger.info("Running in infinite streaming mode.")
        endtime =float("inf")
    else:
        endtime = time.time() + duration
    
    retries = 0
     
    while True:
        
        if stop_streaming.is_set():
            logger.info("Streaming stopped")
            break
        
        if time.time() < endtime:
            logger.info("Streaming stopped")
            break
        
        sensor_data = generate_data(features_config=features_config)
        
        try:
            response = requests.post(DETECTION_SERVICE_URL, json=sensor_data, timeout=6)
            if response.status_code == 200:
                logger.info(f"data: {sensor_data} send to {DETECTION_SERVICE_URL} successfully")
                retries = 0
            else:
                logger.error(f"Detection service error: {response.status_code}, {response.text}")
                raise requests.exceptions.RequestException(f"Detection service error: {response.status_code}")
            waiting_time = interval
            
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error(f"Error while calling the detection service. Attempt no.: {retries}/{MAX_RETRIES}: {str(e)}")
        
            if retries >= MAX_RETRIES:
                logger.critical("Detection service not reachable. Stopping attempts.")
                break
            else:
                waiting_time = INITIAL_WAIT_TIME * (WAIT_TIME_MULTIPLIER ** (retries -1))
                logger.info(f"Retrying in {waiting_time} seconds.")
        
        except Exception as e:
            logger.critical(f"Error while generating or sending data: {str(e)}")
            retries = MAX_RETRIES        
                
        time.sleep(waiting_time)

stream_app = Flask(__name__)

def start_streaming():
    global streaming_status
    
    if not streaming_status:
        streaming_status = True
        stop_streaming.clear()
        thread = Thread(target=stream_data, daemon=True)
        thread.start()
    else:
        logger.info("Streaming is already active.")

@stream_app.route("/restart_streaming", methods=["POST"])
def restart_stream():
    logger.info("Restarting the application.")
    start_streaming()
    return jsonify({"message": "Streaming restarted."}, 200)

if __name__ == "__main__":
    start_streaming()
    stream_app.run(host="0.0.0.0", port=5000)

