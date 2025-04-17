from fastapi import FastAPI
import pandas as pd
from core import simple_moving_avg

app = FastAPI()

@app.get("/strategy/run")
def run_strategy():
    df = pd.DataFrame({
        'close': [100 + i for i in range(30)]  # 30 days of fake price data
    })
    result = simple_moving_avg(df)
    result = result.replace([float('inf'), float('-inf')], None)
    result = result.dropna()
    return result.tail().to_dict(orient="records")
