"""
Generates a dataset for training unsupervised anomaly detection algorithms.
Default sample size: 50,000
Default timestamp intervall: 5sec
Requires min. 1 feature as input, but can have multiple.
Features are added/modified/deleted in features_config.
See description below for features.
"""

import numpy as np
import pandas as pd

from datetime import datetime, timedelta


def generate_data_per_feature(distribution: str, params, sample_size: int):
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

def generate_dataset(sample_size: int =50000, timestamp_interval: int =5, features_config=None):
    """
    Generates a dataset according to the loaded features_config.
    Args:
        sample_size (int, default=50000): Defines the number of data generated.
        timestamp_interval (int, default=5): Defines the timestamp, starting from "now" in sec.
        features_config(default=None): Contains the base information for the data generation (e.g. the distribution etc.)
        
    Returns:
        df (pd.DataFrame): Contains the generated data.
    """
    if features_config == None:
        raise ValueError("No features found. Add at least one feature to the configuration.")
    
    data = {}
    
    start_time = datetime.now()
    
    for feature in features_config.values():
        feature_name = feature['name']
        distribution = feature['distribution']
        params = feature['params']
        anomaly_ratio = feature['anomaly_ratio']
        anomaly_range = feature['anomaly_range']
        drift = feature['drift']
        
        feature_data = generate_data_per_feature(
            distribution=distribution,
            params=params,
            sample_size=sample_size
        )
        
        anomalies = np.random.rand(sample_size) < anomaly_ratio
        feature_data[anomalies] = np.random.uniform(anomaly_range[0], anomaly_range[1], size=anomalies.sum())        
        feature_data += np.arange(sample_size) * drift
        data[feature_name] = feature_data

    
    timestamps = [start_time + timedelta(seconds=i * timestamp_interval) for i in range(sample_size)]
    data["timestamp"] = timestamps
    df = pd.DataFrame(data)
    
    return df
           
# Config of features
"""  
    Feature configuration as input for synthetical data.
    ----
    Keys:
    distribution: Specifies the distribution for each feature.
        - normal: Generates data based on a normal (Gaussian) distribution.
        - uniform: Generates data based on a uniform distribution.
        - exponential: Generates data based on an exponential distribution.
        - poisson: Generates data based on a Poisson distribution.
        - lognormal: Generates data based on a log-normal distribution.
        - gamma: Generates data based on a Gamma distribution.
        - beta: Generates data based on a Beta distribution.
        - weibull: Generates data based on a Weibull distribution.
        - triangular: Generates data based on a triangular distribution.
        - chisquare: Generates data based on a Chi-Squared distribution.
        
    params: Specifies the parameters defining the distribution.
        - for normal: {"mean": float, "std": float} -> mean and standard deviation.
        - for uniform: {"low": float, "high": float} -> lower and upper bounds.
        - for exponential: {"scale": float} -> scale parameter (inverse of rate).
        - for poisson: {"lam": float} -> mean number of events per interval.
        - for lognormal: {"mean": float, "sigma": float} -> mean and standard deviation of the natural logarithm.
        - for gamma: {"shape": float, "scale": float} -> shape and scale parameters.
        - for beta: {"a": float, "b": float} -> alpha and beta parameters.
        - for weibull: {"a": float} -> shape parameter.
        - for triangular: {"left": float, "mode": float, "right": float} -> minimum, most likely, and maximum values.
        - for chisquare: {"df": float} -> degrees of freedom.
    
    drift: float -> Specifies the drift of the feature. Set to 0 for no drift.
    
    anomaly_range: tuple -> Range where the anomalies are distributed.
    
    anomaly_ratio: float -> Ratio of anomalies. Consider that the anomalies are distributed uniform.
    A ceratin number of anomalies will always fall in the accepted area.  
"""

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


if __name__ == "__main__":
    # Default setting is 5
    timestamp_interval = 5
    
    # Default setting is 50,000
    datasets = [
        (50000, "src/data/synthetic_data/synthetic_training_data.csv"),
        (12500, "src/data/synthetic_data/synthetic_test_data.csv"),
        (25000, "src/data/synthetic_data/synthetic_validation_data.csv")
    ]
    
    for sample_size, output_file in datasets:
        df = generate_dataset(sample_size=sample_size, timestamp_interval=timestamp_interval, features_config=features_config)
        df.to_csv(output_file, index=False, encoding='utf-8')
        
    print("Data generated")