# Step 1: Anomaly detection training model

--> Add a drift to validation data!


# Step 2: Create a data generator file, that produces every 5sec a set of data.
- create the file in a manner that it is easy adjustable
- create the file in a manner that it can be terminated at any time, but max. runs 2min
- create the file in a manner that it is callable via API

# Step 3: Create a anomaly detection based on the training data
- create the file in a manner that it is callable via API
- the file should rely on the weights from the training process

# Step 4: Package both files (data generator & anomaly detection)
- consider the pacakge of the pre-trained weights as well
- preparation for Cloud Environment

# Step 5: Setup the cloud environment for the data generator
- upload the data generator to the cloud environment
- RUN A TEST WHERE THE LOCAL ANOMALY DETECTOR CALLS THE API (if possible)

# Step 6: Setup the cloud environment for the anomaly detector