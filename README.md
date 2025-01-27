# Anomaly Detection - from model to production (on AWS)

This repository contains all files and scripts to create a simple ML model to detect anomalies and upload the system to a cloud environment.

# **Table of Contents**

1. [**Background Information**](#background-information)  
&nbsp;&nbsp;&nbsp;&nbsp;*Brief project description..*  

2. [**Environment Setup**](#environment-setup)  
&nbsp;&nbsp;&nbsp;&nbsp;*Listing of prerequisites and tools used for this project.*  

3. [**Architecture Overview**](#architecture-overview)  
&nbsp;&nbsp;&nbsp;&nbsp;*Illustration of the underlying system architecture and its components.*

4. [**Data**](#data)  
   - 4.1 **Data Generation for Training and Testing**  
     &nbsp;&nbsp;&nbsp;&nbsp;*Description of the training and testing data generation.*  
   - 4.2 **Data Stream for Production**  
     &nbsp;&nbsp;&nbsp;&nbsp;*Detail of a data stream as input for the model in production.*

5. [**Machine Learning Model**](#machine-learning-model)  
   - 5.1 **Model Selection**  
     &nbsp;&nbsp;&nbsp;&nbsp;*Preconditions for the model and selection process.*  
   - 5.2 **Model Training**  
     &nbsp;&nbsp;&nbsp;&nbsp;*Description of the model training process.*  
   - 5.3 **Model Testing**  
     &nbsp;&nbsp;&nbsp;&nbsp;*Validation of the model's performance.*  
   - 5.4 **Model Deployment**  
     &nbsp;&nbsp;&nbsp;&nbsp;*Integration of the pre-trained model in a production environment.*

6. [**Dashboard and Monitoring**](#dashboard-and-monitoring)  
   - 6.1 **Monitoring the Production Environment**  
     &nbsp;&nbsp;&nbsp;&nbsp;*Layout and description of the dashboard for monitoring.*  
   - 6.2 **Monitoring the Model’s Performance**  
     &nbsp;&nbsp;&nbsp;&nbsp;*Monitoring the model performance during production.*

7. [**Cloud Deployment**](#cloud-deployment)  
   - 7.1 **Cloud Architecture**  
     &nbsp;&nbsp;&nbsp;&nbsp;*Diagram and explanation of the AWS-cloud architecture.*  
   - 7.2 **Setting Up the Cloud Environment**  
     &nbsp;&nbsp;&nbsp;&nbsp;*Description of the deployment process.*

---

# **Background Information**
The project aims to simulate a production environment where three sensors send data to an anomaly detection algorithm. This algorithm evaluates the input of the sensors and forwards the results to a dashboard, which can be used to monitor the production line. In order to simulate the sensors a data stream is used, generating synthetical data.  
This project includes the whole process from data generation to deployment of the system on a cloud environment.  

# **Environment Setup**
Before describing the implementation of the above mentioned project the prerequisites and tools used are listed below:
- **Linux (native or WSL): This project is designed to run on Linux. It is recommended to use a Linux machine or WSL if you are using Windows. Running the project on Windows or macOS can cause problems. WSL can be installed following this [guide](https://learn.microsoft.com/de-de/windows/wsl/install).
- **Python:** This project requires Python 3.7 or later.
- **Docker:** Docker is needed to containerize the system. It is also possible to run it only locally. Then Docker is not required.
- **Terraform:** Terraform is used to create the cloud infrastructure on AWS. It is only needed if the system is be deployed on the cloud.
- **AWS account:** An AWS account is required for deployment. Like Terraform, it is only necessary if the system is to be deployed on the cloud.

To install the required dependencies to run this project locally, run the following command:
```bash
pip install -r requirements.tx
```

# Architecture Overview

![Architecture](images\simplified_project_architecture.png)

The system architecture consists of three main components: Data Stream, Analysis and Monitoring. Each component is developed as an independent application to ensure modularity and flexibility.  
1. Data Stream: This application simulates the data generation and any necessary preprocessing. It is designed to be replaceable by real-world production data, without influencing the other components.
2. Analysis: The anomaly detection algorithm, including the pre-trained weights are implemented in this application.
3. Monitoring: The last application provides a dashboard to track the detection results and the performance of the model. In a real-world application it can be enriched with other production relevant data or be replaced by already existing dashboards.

The development focuses on the independence of the components in order to be able to exchange them when necessary and minimizing the need for change in the other components.

The cloud architecture for this project is described in [Cloud Deployment](#cloud-deployment).

# Data

## General assumptions about the data
The data used for training and streaming is not based on real-world data, but created synthetical based on underlying distributions.  
Furthermore the data used for the training is not annotated and thus the anomaly detection requires an unsupervised model, described in [Machine Learning Model](#machine-learning-model).  
All datasets (training, testing and streaming) are based on the same underlying distributions, which are defined as follows:  

Temperature:  
- Distribution: normal (mean: 22, std: 2)
- Anomaly injection: uniform (range: 15-30, ratio: 0.01)

Humidity:
- Distribution: normal (mean: 50, std: 5)
- Anomaly injection: uniform (range: 30-70, ratio: 0.01)

Noise Level:
- Distribution: normal (mean: 80, std: 5)
- Anomaly injection: uniform (range: 60-100, ratio: 0.02)

The features are defined in [features_config.json](src\production\stream_data\features_config.json).  
The supported distributions are described [here](CONFIGURE_FEATURES.md).  

The training and and data stream should be build in a manner that more "sensors" can be added to the features configuration. After running the training, testing etc. the system should still be working, without further adjustments.  

## Data Generation for Training and Testing
The data for training and testing is created by running the [data_generator.py](src\data_generation\data_generator.py).  
It uses the configuration file for the features as described above and generates three datasets - for training, testing and validation.  
The synthetical data is stored as a CSV-file [here](src\data\synthetic_data).  
In this current version 50,000 rows are generated for training. The amount can be adjusted within the data generator file.  

The data contains a timestamp, a value for each simulated sensor (temperature, humidity and noise level).  

To review the generated data a second script is added, which can be used to visualize the features in a diagram.  

## Data Stream for Production
The data stream generates data and sends it to the detection service, i.e. the anomaly detection algorithm using flask.  
This application simulates already preprocessed sensor data (in case the sensor data needs to be encoded etc.) and sends it as a package, including all values needed for the anomaly detection algorithm and a timestamp.  

**Restrictions**:  
The data stream currently uses a "sleep" time of one second and stops automatically after 10min.  
The reason is that the data stream is deployed on AWS and thus causes costs. In order to limit this these restrictions are built in.  
[data_stream.py](src\production\stream_data\stream_data.py) contains instructions how to adjust or remove the limitations.  

# Machine Learning Model
## Model Selection
Based on the data generated the models are restricted to unsupervised models. 
For this project two different models are trained, KMeans Clustering and One Class Support Vector Machine.  

- K-Means: Is generally a simple model and easy to understand, making it also explainable.
- One Class SVM: Can detect more complex anomaly patterns.  

Since the main focus of this project is on the development of the whole system and not of a elaborate ML model only these two models are considered.  

Information about the models:  
[Medium](https://medium.com/simform-engineering/anomaly-detection-with-unsupervised-machine-learning-3bcf4c431aff)  
[Builtin](https://builtin.com/machine-learning/anomaly-detection-algorithms)  

## Model Training


## Model Testing


## Model Deployment


# Dashboard and Monitoring

# Cloud Deployment