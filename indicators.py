import pandas as pd

def sma(df, window = 20, column = 'close'):
    """
    단순 이동 평균 (Simple Moving Average, SMA) 계산
    """
    return df[column].rolling(window=window).mean()

def ema(df, window = 20, column = 'close'):
    """
    지수 이동 평균 (Exponential Moving Average, EMA) 계산
    """
    return df[column].ewm(span=window, adjust=False).mean()

def rsi(df, period = 14, column = 'close'):
    """
    상대 강도 지수 (Relative Strength Index, RSI) 계산
    """
    delta = df[column].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs)) # Returned : rsi

def macd(df, fast_period = 12, slow_period = 26, signal_period = 9, column = 'close'):
    """
    이동 평균 수렴 발산 (Moving Average Convergence Divergence, MACD) 계산
    """
    ema_fast = ema(df, fast_period, column)
    ema_slow = ema(df, slow_period, column)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({
        'MACD_Line': macd_line,
        'MACD_Signal_Line': signal_line,
        'MACD_Histogram': histogram
    }, index = df.index)

# (To be added) def bollinger_bands(df, window = 20, num_std = 2, column = 'close')