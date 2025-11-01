## binance에서 과거 데이터 수집(시가, 고가, 저가, 종가, 거래량) 수집, CSV로 로컬 캐싱 
import os
import pandas as pd
import ccxt
from datetime import datetime, timedelta

DATA_DIR = "data"
os.makdeirs(DATA_DIR,exist_ok=True)

def fetch_ohlcv(symbol="BTC/USDT", timeframe ="1h", since_days = 180, exchange_name = "binance" ):
  """
  Binance에서 OHLCV 데이터 가져오기
  """
  exchange = getattr(ccxt, exchange_name)()
  since = exchange.parse8601((datetime.utcnow() - timedelta(days=since_days)).strftime('%Y-%m-%dT%H:%M:%S'))

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

