import pandas as pd
from core import simple_moving_avg

def test_sma_strategy():
    df = pd.DataFrame({'close': [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]})
    result = simple_moving_avg(df, short=3, long=5)

    assert 'short_ma' in result.columns
    assert 'long_ma' in result.columns
    assert 'signal' in result.columns
    assert result['signal'].iloc[-1] in [0, 1]