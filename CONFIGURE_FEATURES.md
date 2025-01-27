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

drift: float -> Specifies the drift of the feature. Set to 0 for no drift. Not tested. Stick to zero to ensure smooth running.

anomaly_range: tuple -> Range where the anomalies are distributed.  

anomaly_ratio: float -> Ratio of anomalies. Consider that the anomalies are distributed uniform.  
A certain number of anomalies will always fall in the accepted area.  

The features config can be found [here](src\production\stream_data\features_config.json).  