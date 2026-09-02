import pandas as pd
df = pd.read_csv("downtime_logs.csv")
print(df.head())
print("shape: {df.shape}")
print("Columns:", df.columns)
print(df.describe())