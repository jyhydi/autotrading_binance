import pandas as pd

def generate_signals(df):
  """
  지표 기반 매매 신호 생성
  반환: 매수(+1), 매도(-1), 유지(0)
  """
  df = df.copy()

  #initial signal set to zero
  df["signal"] = 0

  #RSI 기반 신호
  if "RSI" in df.columns:
      df.loc[df["RSI"] < 30, "signal"] += 1  # 매수 신호
      df.loc[df["RSI"] > 70, "signal"] += -1 # 매도 신호

  #MACD 기반 신호
  if "MACD" in df.columns and "MACD_Signal" in df.columns:
      df.loc[df["MACD"] > df["MACD_Signal"], "signal"] += 1  # 매수 신호
      df.loc[df["MACD"] < df["MACD_Signal"], "signal"] += -1 # 매도 신호

  #볼린저 밴드 기반 신호
  if "Bollinger_Upper" in df.columns and "Bollinger_Lower" in df.columns:
      df.loc[df["close"] < df["Bollinger_Lower"], "signal"] += 1  # 매수 신호
      df.loc[df["close"] > df["Bollinger_Upper"], "signal"] += -1 # 매도 신호

  #신호 값 정규화
  df["signal"] = df["signal"].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
  return df["signal"]

if __name__ == "__main__":
    # 테스트 실행
    from data_handler import get_data
    from indicators import rsi, macd, bollinger_bands

    #데이터 로드
    df = get_data("BTC/USDT", "1h", 30)

    #지표 계산
    df["RSI"] = rsi(df)
    macd_df = macd(df)
    df["MACD"] = macd_df["MACD_Line"]
    df["MACD_Signal"] = macd_df["MACD_Signal_Line"]
    bb_df = bollinger_bands(df)
    df["Bollinger_Upper"] = bb_df["Bollinger_Upper"]
    df["Bollinger_Lower"] = bb_df["Bollinger_Lower"]

    #신호 생성
    signals = generate_signals(df)
    print(signals.tail(20)) # 마지막 5개 신호 출력

