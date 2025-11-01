## binance에서 과거 데이터 수집(시가, 고가, 저가, 종가, 거래량) 수집, CSV로 로컬 캐싱 
import os
import pandas as pd
import ccxt
from datetime import datetime, timedelta, timezone

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_ohlcv(symbol="BTC/USDT", timeframe ="1h", since_days = 180, exchange_name = "binance" ): 
    """
    Binance에서 OHLCV 데이터 가져오기
    """
    exchange = getattr(ccxt, exchange_name)()
    # use timezone-aware UTC datetime to avoid deprecation warnings
    since = exchange.parse8601((datetime.now(timezone.utc) - timedelta(days=since_days)).strftime('%Y-%m-%dT%H:%M:%S'))

    all_data = []
    while True:
        candles = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
        if not candles:
            break
        all_data.extend(candles)
        since = candles[-1][0] + 1  # 마지막 타임스탬프 이후부터 시작
        if len(candles) < 1000:
            break
    
    df = pd.DataFrame(all_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('datetime', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']] 
    return df

def save_to_csv(df, filename):
    """
    DataFrame을 CSV 파일로 저장
    """
    filepath = os.path.join(DATA_DIR, filename)
    # ensure index has a name so load_from_csv can use index_col='datetime'
    if df.index is not None:
        try:
            df.index.name = 'datetime'
        except Exception:
            pass
    df.to_csv(filepath)
    print(f"Data saved to {filepath} (len={len(df)} rows)")

def load_from_csv(filename):
    """
    CSV 파일에서 DataFrame 로드
    """
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        # try loading with explicit index name first, fall back to using the first column
        try:
            df = pd.read_csv(filepath, index_col='datetime', parse_dates=True)
        except Exception:
            df = pd.read_csv(filepath, parse_dates=True)
            # if the first column looks like a datetime, set it as the index
            first_col = df.columns[0]
            try:
                df[first_col] = pd.to_datetime(df[first_col])
                df.set_index(first_col, inplace=True)
            except Exception:
                pass
        print(f"Data loaded from {filepath} (len={len(df)} rows)")
        return df
    else:
        print(f"File not found : need to fetch from API")
        return None
    
def get_data(symbol="BTC/USDT", timeframe ="1h", since_days = 180, exchange_name = "binance" ):
    """
    CSV에서 데이터 로드, 없으면 API에서 가져와 저장
    """
    filename = f"{symbol.replace('/','_')}_{timeframe}.csv"
    df = load_from_csv(filename)
    if df is None:
        df = fetch_ohlcv(symbol, timeframe, since_days, exchange_name)
        save_to_csv(df, filename)
    return df

if __name__ == "__main__":
    # Test running
    df = get_data("BTC/USDT", "1h", 30)
    print(df.tail())

