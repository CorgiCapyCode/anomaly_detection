"""
This script serves to train several unsupervised models with a dataset.
The trained models are:

KMeans Clustering
One Class Support Vector Machines
"""

import joblib
import numpy as np
import os
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.svm import OneClassSVM

os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LOKY_MAX_CPU_COUNT"] = "14"

def load_dataset(file_path: str):
    """
    Loads a dataset for the training of the algorithm.
    There is no data split required. See data_generator.py
    
    Args:
        file_path (str): Path to the dataset containing the training data.
    """
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"Error when trying to load the csv file. Code: {e}")
        return None

def kmeans_training(df: pd.DataFrame, path: str, clusters: int =3):
    """
    Trains a KMeans model.
    
    Args:
        df (pd.DataFrame): The dataset for training.
        path (str): The path to store the weights/parameters of the model.
        clusters (int, default = 3): The number of clusters for the KMeans model.
    
    """
    if df is None or df.empty:
        raise ValueError("No valid input for the dataframe found.")
    
    features = df.select_dtypes(include=[np.number])
    if features.empty:
        raise ValueError("No valid input for the features found.")
    
    kmeans = KMeans(n_clusters=clusters, random_state=17)
    kmeans.fit(features)
    
    path = f"{path}/kmeans_model.pkl"
    
    joblib.dump(kmeans, path)
    
def ocsvm_training(df: pd.DataFrame, path: str, kernel: str ="rbf", nu: float = 0.04, gamma: str ="scale"):
    """
    Trains a One-Class Support Vector Machine.
    Args:
        df (pd.DataFrame): The dataset for training.
        path (str): The path to store the weights/parameters of the model.
        kernel (str, default = "rbf"): Hyperparameter for the OCSVM.
        nu (float, default = 0.04): Hyperparameter for the OCSVM.
        gamma (str, default = "scale"): Hyperparameter for the OCSVM.
    """
    
    if df is None or df.empty:
        raise ValueError("No valid input for the dataframe found.")
    
    features = df.select_dtypes(include=[np.number])
    if features.empty:
        raise ValueError("No valid input for the features found.")
    
    ocsvm = OneClassSVM(kernel=kernel, nu=nu, gamma=gamma)
    ocsvm.fit(features)
    
    path=f"{path}/ocsvm_model.pkl"
    joblib.dump(ocsvm, path)

if __name__=="__main__":
    file_path = "src/data/synthetic_data/synthetic_training_data.csv"
    df = load_dataset(file_path=file_path)
    
    # Path to the directory to store the models.
    # The model name and type are added automatically.
    path = "src/production/anomaly_detection"
    
    # KMeans
    clusters = 1
    kmeans_training(df=df, path=path, clusters=clusters)
    print("Finished training KMeans-model.")
    
    # One-Class Support Vector Machine
    kernel  ="rbf"
    nu = 0.04
    gamma = "scale"
    ocsvm_training(df=df, path=path, kernel=kernel, nu=nu, gamma=gamma)
    print("Finished training OCSVM-model.")
    
    