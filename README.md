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



# Data


# Machine Learning Model

# Dashboard and Monitoring

# Cloud Deployment