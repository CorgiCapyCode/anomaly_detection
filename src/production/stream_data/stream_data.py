import logging
import numpy as np
import os
import random
import requests
import time

from datetime import datetime
from flask import Flask, jsonify, request
from threading import Thread, Timer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DETECTION_SERVICE_URL = os.getenv("DETECTION_SERVICE_URL", "http://anomaly_detection_container:5001/anomaly_detection")

stop_flag = False

MAX_RETRIES = 5
INITIAL_WAIT_TIME = 2
WAIT_TIME_MULTIPLIER = 2

def generate_data_per_feature(distribution: str, params, sample_size: int =1):
    """
    Generates the data for the feature according to the configuration.
    
    Args:
        distribution(str): Defines the type of distribution for the data generation.
        params: Defines the parameters for the distribution.
        sample_size(int): Defines the number of data points.
    """
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

def stream_data(features_config):
    """
    Generates a stream of data according to the features configuration.
    Args:
        features_config: Defines which features with which porperties are to be generated.
        
    Return:
        A data point with the features.
    """
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

            value = generate_data_per_feature(
                distribution=distribution,
                params=params,
                sample_size=1
            )[0]

        data_point[feature_name] = value

    return data_point

features_config = {
    "temperature": {
        "name": "temperature",
        "distribution": "normal",
        "params": {
            "mean": 22,
            "std": 2,
        },
        "drift": 0,
        "anomaly_range": (15, 30),
        "anomaly_ratio": 0.01,
    },
    "humidity": {
        "name": "humidity",
        "distribution": "normal",
        "params": {
            "mean": 50,
            "std": 5,
        },
        "drift": 0,
        "anomaly_range": (30, 70),
        "anomaly_ratio": 0.01,
    },
    "noise_level": {
        "name": "noise_level",
        "distribution": "normal",
        "params": {
            "mean": 80,
            "std": 5,
        },
        "drift": 0,
        "anomaly_range": (60, 100),
        "anomaly_ratio": 0.02,
    },
}

stream_app = Flask(__name__)

#@stream_app.route("/generate", methods=["GET"])
def generate_and_detect():
    global stop_flag
    retries = 0
    while retries < MAX_RETRIES and not stop_flag:
        try:
            data_point = stream_data(features_config)
            response = requests.post(DETECTION_SERVICE_URL, json=data_point)
            
            if response.status_code == 200:
                detection_result = response.json()
                logger.info(f"data: {data_point} -> detection result: {detection_result}")
                retries = 0
            else:
                logger.error(f"Detection service error: {response.status_code}, {response.text}")
                raise requests.exceptions.RequestException(f"Detection service error: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            retries += 1
            logger.error(f"Error while calling the detection service. Attempt no.: {retries}/{MAX_RETRIES}: {str(e)}")
            
            if retries >= MAX_RETRIES:
                logger.critical("Detection service not reachable. Stopping attempts.")
                break
            else:
                waiting_time = INITIAL_WAIT_TIME * (WAIT_TIME_MULTIPLIER ** (retries -1))
                logger.info(f"Retrying in {waiting_time} seconds.")
                time.sleep(waiting_time)
        
        except Exception as e:
            logger.critical(f"Error while generating or sending data: {str(e)}")
            retries = MAX_RETRIES
              
        time.sleep(1.0)

def start_stream():
    thread = Thread(target=generate_and_detect)
    thread.start()
    
    timer = Timer(600, stop_stream)
    timer.start()
    
    return jsonify({"message": "Stream started. Generates every second one set of values."}), 200

def stop_stream():
    global stop_flag
    stop_flag = True
    logger.info("Stream stopped after 10min")

if __name__ == "__main__":
    start_stream()
    stream_app.run(host="0.0.0.0", port=5000)