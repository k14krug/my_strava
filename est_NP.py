import pandas as pd
import statsmodels.api as sm

# 1) Load rides that have known NP
df = pd.read_csv("NP.csv")

# 2) (Optional) Add a column for speed^3 if you suspect aerodynamic drag is important
df["speed_cubed"] = df["average_speed"] ** 3

# 3) Define your predictor columns (X) and target column (y)
X = df[["average_speed", "speed_cubed", "distance", "total_elevation_gain"]]
X = sm.add_constant(X)  # adds the intercept term
y = df["np"]

# 4) Fit a linear regression model
model = sm.OLS(y, X).fit()

# 5) Inspect the results
print(model.summary())
print("Coefficients:")
print(model.params)
