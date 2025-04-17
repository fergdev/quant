import pandas as pd
import os
from core import simple_moving_avg

if __name__ == "__main__":
    file_path = "/data/sample_prices.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        result = simple_moving_avg(df)
        print(result.tail())
    else:
        print(f"No data file found at {file_path}. Skipping execution.")