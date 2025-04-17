import pandas as pd

def simple_moving_avg(df: pd.DataFrame, short=5, long=20) -> pd.DataFrame:
    df = df.copy()
    df['short_ma'] = df['close'].rolling(short).mean()
    df['long_ma'] = df['close'].rolling(long).mean()
    df['signal'] = (df['short_ma'] > df['long_ma']).astype(int)
    return df