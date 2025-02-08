"""
Uses a dataset to test the trained models.
The test is no deep-dive. The main functionalities are:
1. Evaluating the data of the test set and adding "is_anomaly" (bool) to the data.
2. Merging both results for manual check for differences. No automatic check is done.
3. Visualization of the anomalies found in with the kmeans model.
The visualization is designed for the three standard features (temperature, humidity and noise_level).
"""

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mpl_toolkits.mplot3d import Axes3D
from sklearn.metrics import pairwise_distances

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
        return model
    except Exception as e:
        print(f"Error when trying to load the model. Code: {e}")
        return None        


def kmeans_testing(test_data: pd.DataFrame, model, threshold: float):
    """
    Tests the KMeans Model.
    Args:
        test_data (pd.DataFrame): The testing data.
        model: The model data.
        threshold: The threshold when a data point is considered to be an outlier.
        
    Return:
        results (pd.DataFrame): The dataframe extended with the distance and the key if outlier or not.
    """
    if test_data is None or test_data.empty:
        raise ValueError("No valid input for test_data. ")
    
    if model is None:
        raise ValueError("No valid input for the model found.")
    
    results = test_data.copy()
    features = results.select_dtypes(include=[np.number])
    distances = pairwise_distances(features, model.cluster_centers_, metric="euclidean")
    min_distances = np.min(distances, axis=1)
    
    results["min_distance"] = min_distances
    results["anomaly"]= min_distances > threshold
    
    return results


def ocsvm_testing(test_data: pd.DataFrame, model):
    """
    Test the One Support Vector Machine model.
    Args:
        test_data (pd.DataFrame): Dataset with the testing data.
        model: Contains the model data.
    Return
        results (pd.DataFrame): The dataframe extended with the annotation of outliers/anomalies.
    """
    
    if test_data is None or test_data.empty:
        raise ValueError("No valid input for test_data. ")
    
    if model is None:
        raise ValueError("No valid input for the model found.")
    
    results = test_data.copy()
    features = results.select_dtypes(include=[np.number])
    
    predictions = model.predict(features)
    results["anomaly"] = predictions == -1
    
    return results


def base_metrics(df: pd.DataFrame):
    """
    Calculates the standard metrics to compare the model results.
    
    Args:
        df (pd.DataFrame): Test results with the anomaly information.
        
    Return:
        metrics (dict): Containing the test results
    """
    
    if df is None or df.empty:
        raise ValueError("No valid input for the dataframe. ")
        
    total_points =  len(df)
    anomaly_count = df["anomaly"].sum()
    anomaly_ratio = anomaly_count / total_points
    
    metrics = {
        "total_points": total_points,
        "anomaly_count": anomaly_count,
        "anomaly_ratio": anomaly_ratio 
    }
    
    return metrics

  
def result_comparison(kmeans_results: pd.DataFrame, ocsvm_results: pd.DataFrame):
    """
    Compares the results of Kmeans and OCSVM.
    Args:
        kmeans_results (pd.DataFrame): The annotated data from testing the KMeans-model.
        ocsvm_results (pd.DataFrame): The annotated data from testing the OCSVM-Model.    
    """
    # Merge the results on the timestamp in order to compare the predictions.
    merged_results = pd.merge(
        kmeans_results[['timestamp', 'anomaly']],
        ocsvm_results[['timestamp', 'anomaly']],
        on='timestamp',
        suffixes=('_kmeans', '_ocsvm')
    )
        
    merged_results["match"] = merged_results["anomaly_kmeans"] == merged_results["anomaly_ocsvm"]

    kmeans_anomalies = merged_results["anomaly_kmeans"].sum()
    ocsvm_anomalies = merged_results["anomaly_ocsvm"].sum()    
    only_kmeans_anomaly = ((merged_results["anomaly_kmeans"] == 1) & (merged_results["anomaly_ocsvm"] == 0)).sum()
    only_ocsvm_anomaly = ((merged_results["anomaly_kmeans"] == 0) & (merged_results["anomaly_ocsvm"] == 1)).sum()
    both_anomaly = ((merged_results["anomaly_kmeans"] == 1) & (merged_results["anomaly_ocsvm"] == 1)).sum()

    intersection_over_union = both_anomaly / (kmeans_anomalies+ocsvm_anomalies-both_anomaly)
    
    merged_results.to_csv("src/data/test_results/merged_lists.csv")
    print("Comparison Results:")
    print(f"Total anomalies (K-Means & OCSVM): {kmeans_anomalies}       {ocsvm_anomalies}")
    print(f"Only one model (K-Means & OCSVM):  {only_kmeans_anomaly}        {only_ocsvm_anomaly}")
    print(f"Anomalies in both: {both_anomaly}")
    print(f"Intersection over Union (Jaccard-Index): {intersection_over_union}")


def kmeans_visualization(df: pd.DataFrame, kmeans_model, path: str, num_points: int =100):
    """
    Creates a 3D visualization of the kmeans test results based on the standard sensor input.
    Requires temperature, humidity and noise level as input.
    Args:
        df (pd.DataFrame): The test results as basis for the 3D visualization.
        kmeans_model: The model to visualize the centroids.
        num_points (int, default=100): The number of random points visualized.
    """
    feature_columns = ["temperature", "humidity", "noise_level"]
    features = df[feature_columns]
    anomalies = df[df['anomaly'] == True].reset_index(drop=True)
    
    feature_columns = ["temperature", "humidity", "noise_level"]
    features = df[feature_columns]
    anomalies = df[df['anomaly'] == True].reset_index(drop=True)
    
    centroids = kmeans_model.cluster_centers_[:, :3]

    fig_1 = plt.figure(figsize=(12, 12))
    ax_1 = fig_1.add_subplot(111, projection="3d")
    
    ax_1.scatter(
        anomalies[feature_columns[0]], anomalies[feature_columns[1]], anomalies[feature_columns[2]],
        c="pink", label="Anomalies", alpha=0.9
    )

    ax_1.scatter(
        centroids[:, 0], centroids[:, 1], centroids[:, 2],
        c="red", marker="X", s=200, label="Centroids"
    )

    ax_1.set_title("3D Visualization: Anomalies and Centroids")
    ax_1.set_xlabel(feature_columns[0])
    ax_1.set_ylabel(feature_columns[1])
    ax_1.set_zlabel(feature_columns[2])
    ax_1.legend()
    
    save_path = f"{path}/kmeans_anomalies.png"
    plt.savefig(save_path, format="png", dpi=300)
    plt.close(fig_1)


if __name__ == "__main__":

    # Load Testing data
    test_data_path = "src/data/synthetic_data/synthetic_test_data.csv"
    test_data = load_dataset(test_data_path)
    
    # Test KMeans
    kmeans_model_path = "src/production/anomaly_detection/kmeans_model.pkl"
    kmeans_test_results_path = "src/data/test_results/test_results_kmeans.csv"
    image_path="src/data/test_results/img"
    
    kmeans_model = load_model(path=kmeans_model_path)
    df_kmeans = load_dataset(kmeans_test_results_path)
    
    threshold = 13.6
    kmeans_results = kmeans_testing(test_data=test_data, model=kmeans_model, threshold=threshold)
    kmeans_results.to_csv("src/data/test_results/test_results_kmeans.csv", index=False)
    
    # Only to be used for the standard set of sensors - temperature, humidity and noise level.
    kmeans_visualization(df=df_kmeans, kmeans_model=kmeans_model, path=image_path)
    kmeans_results = base_metrics(df=df_kmeans)
    print("KMeans - Results:")
    print(kmeans_results)    

    # Test One Class Support Vector Machine
    ocsvm_model_path = "src/production/anomaly_detection/ocsvm_model.pkl"
    ocsvm_test_results_path = "src/data/test_results/test_results_ocsvm.csv"
    
    ocsvm_model = load_model(ocsvm_model_path)
    df_ocsvm = load_dataset(ocsvm_test_results_path)
    
    ocsvm_results = ocsvm_testing(test_data=test_data, model=ocsvm_model)
    ocsvm_results.to_csv("src/data/test_results/test_results_ocsvm.csv", index=False)
    
    ocsvm_results = base_metrics(df=df_ocsvm)
    print("OCSVM-Results:")
    print(ocsvm_results)     
    
    # Create file for comparing.
    result_comparison(kmeans_results=df_kmeans, ocsvm_results=df_ocsvm)    
    print("Model testing completed")
