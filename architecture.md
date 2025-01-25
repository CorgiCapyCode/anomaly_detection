# Data generation
## Characteristics/features
| Feature       | Description                   | Format                | Distribution  | Mean  | St    |
|---------------|-------------------------------|-----------------------|---------------|-------|-------|
| timestamp     | date + time of the data       | YYYY-MM-DD HH:MM:SS   | n/a           | n/a   | n/a   |
| temperature   | Value of temperature sensor   | float [°C]            | Normal        | 22    | 2     |
| humidity      | Value of the humidity sensor  | float in percentage   | Normal        | 50    | 5     |
| noise level   | Noise level of the machine    | float [db]            | Normal        | 80    | 5     |


## Training data
File: data_generator.py \
Data generated for training of the machine learning models. \
Number of data points: 20,000. \
Used for local training of the algorithm. Dataset uploaded to the repository, not deployed on the cloud. \
The noise level received a drift of 0.001, meaning that the noise increases during the time to simulate machine health. \
The other two features have no dirft (drift = 0.0).

File: data_visualization.py
Only for visualizing the generated data.
Visualizations can be found: [img](img)

## Production data
Data created on demand, when running the program. \
To limit the creation, it will end after TBDmin. \
Script uploaded to the cloud.

