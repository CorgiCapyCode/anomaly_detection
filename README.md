#

## Training / Testing Data Generation
To train and test models synthetic datasets are created.
The data contains three features: temperature, humiditiy and noise level.

[data_generator.py](/src/data_generation/data_generator.py) contains a feature config, which can be used to create the features. \
Furthermore the config defines the distribution, outlier probability and a general drift. \
The default setting for the data generation is 50,000 data points in a time interval of 5sec.\
A testing and validation set are created, with each 12,500 entries are created as well. However, the validation set is currently not used. \

[data_visualization](/src/data_generation/data_visualization.py) is only used to create graphs of the created data. \

## Model Training and Testing
Two models are created and compared on a high-level. Both models use unsupervised learning methods. \
The first model is KMeans that is trained for one cluster (default, can be changed). \
The second model is One Class Support Vector Machine (OCSVM). \

The models are trained with [model_training.py](/src/model_creation/model_training.py). \
The hyperparameters can be adjusted there. \
[Model_training.py](/src/model_creation/model_training.py) saves the models as PKL-files. \

The models are then tested using the [synthetic_test_data.csv](/src/data/synthetic_data/synthetic_test_data.csv). \
This is done in [model_testing.py](/src/model_creation/model_testing.py). \
Note that for KMeans a threshold value for the distance is defined at this stage. \
The file creates for each model an annotated dataset. \

The annotated data is then compared with [result_evaluation.py](/src/model_creation/result_evaluation.py). \
The comparison is on a high-level without introducing special metrics. \

### Results:
Both models show a rate of around 3.5%-4.0% anomalies. \
This is roughly what was to be expected, since: \
The dataset was set to 1% anomalies for the featarues humidity and temperature and 2% for the noise level. \
The anomalies are introduced randomly, meaning that some points might have all three features as anomaly, while others only two or one. \
This leads to slightly lower amount than the sum of all percentages (i.e. <4%). \
The anomalies are introduced as an uniform distribution over a wider range of values (+/- 4x the standard deviation). Due to the use of the uniform distribution some of the values changed to be an anomaly landed within the standard range and thus are not to be classified as anomaly. \
This leads to an even lower amount of anomalies (i.e. <<4%).\
However, a normal distribution already has values that would be classified as outliers. \
This leads to an increased number of anomalies (i.e. >4%).

As conclusion: The around 3.5%-4.0% of detected anomalies seems plausible. \

The results of both models are compared as well. \
It shows that both classify the same data points as anomaly, with the only difference being that the OCSVM model classifies a slightly higher rate (35 out of 12,500) of anomalies. \
These additional points are the only different ones. \

The model ultimately chosen for the project is the One Class Support Vector Machine.

## Continuous Data Generation

## Continuous Detection