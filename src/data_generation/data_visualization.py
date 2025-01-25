"""
This script serves to visualize the generated dataset.
It requires that a timestamp is available in the dataset.
It does not change any data. Just for visualization purposes.
"""
import matplotlib.pyplot as plt
import multiprocessing
import pandas as pd

def save_plot(feature: str, df: pd.DataFrame):
    """
    Saves a plot of each feature's values.
    
    Args:
        feature (str): Feature name
        df (pd.DataFrame): Data for the plots.
    """

    plt.figure(figsize=(40, 6))
    plt.plot(df['timestamp'], df[feature], label=feature)
    plt.title(f'{feature} over Time')
    plt.xlabel('Timestamp')
    plt.ylabel(feature)
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    
    output_file = f'src/data/synthetic_data/img/{feature}_plot_training_data.png'
    plt.savefig(output_file)
    plt.close()

def worker(features: list, df: pd.DataFrame, queue):
    """
    Worker that processes a chunk of features.
    
    Args:
        features (list): List of features.
        df (pd.DataFrame): Data for the plots.
        queue: Queue for the processes.
    """
    for feature in features:
        save_plot(feature=feature, df=df)
        queue.put(f'{feature} saved')

def run_plotting(features: list, df: pd.DataFrame):
    """
    Runs the plotting by using multiple CPU cures.
    
    Args:
        features (list): List of features.
        df (pd.DataFrame): Data for the plots.
    """
    if not features:
        raise ValueError("No valid input for the features found.")
            
    num_processes = multiprocessing.cpu_count()
    chunk_size = max(1, len(features) // num_processes)
    chunks = [features[i:i + chunk_size] for i in range(0, len(features), chunk_size)]

    queue = multiprocessing.Queue()

    processes = []
    for chunk in chunks:
        process = multiprocessing.Process(target=worker, args=(chunk, df, queue))
        processes.append(process)
        process.start()

    for _ in range(len(features)):
        print(queue.get())

    for process in processes:
        process.join()


if __name__ == "__main__":
    
    input_file = "src/data/synthetic_data/synthetic_training_data.csv"
    df = pd.read_csv(input_file)
    
    features = df.columns.tolist()
    features.remove("timestamp")
    
    run_plotting(features=features, df=df)
