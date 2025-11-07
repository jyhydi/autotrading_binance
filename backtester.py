import pandas as pd
from data_handler import get_data
from strategy import generate_signals

def backtest(df, initial_balance=1000000, trade_fee = 0.001):
    """
    단순 백테스팅 함수
    parameter: DataFrame, 초기 자본, 거래 수수료
    반환: 최종 자본, 거래 내역 DataFrame

    """
    df = df.copy()
    
    #setting position
    df["position"] = df["signal"].shift(1).fillna(0)
    
    #calculating return
    df["return"] = df["close"].pct_change().fillna(0)

    #strategy return - including trade fee
    df["strategy_return"] = df["position"] * df["return"]

    #applying trade fee when position changes
    trade_mask = df["position"].diff().abs() > 0
    df.loc[trade_mask, "strategy_return"] -= trade_fee

    # calculating cumulative return & equity
    df["cumulative_return"] = (1 + df["strategy_return"]).cumprod()
    df["cumulative_market_return"] = (1 + df["return"]).cumprod()
    df["equity"] = initial_balance * df["cumulative_return"] 

    return df

if __name__ == "__main__":
  from data_handler import get_data
  from strategy import generate_signals
  
  INITIAL_BALANCE = 1000000
  TRADE_FEE = 0.001

    # 테스트 실행
  df = get_data("BTC/USDT", "1h", 300)

  #신호 생성
  # generate_signals returns a Series of signals; assign it into the DataFrame
  df["signal"] = generate_signals(df)

  # --- diagnostics: inspect why strategy return might be zero ---
  print("signal value counts:\n", df['signal'].value_counts(dropna=False))
  # prepare position and returns (same logic as backtest) for quick inspection
  df['position'] = df['signal'].shift(1).fillna(0)
  print("position value counts:\n", df['position'].value_counts(dropna=False))
  df['return'] = df['close'].pct_change().fillna(0)
  print('return stats:', df['return'].describe())

  result_df = backtest(df, INITIAL_BALANCE, TRADE_FEE)

  """백테스트 결과 출력"""
  print(result_df[["close","signal","position", "strategy_return", "equity", "cumulative_return"]].tail(10))

  final_equity = result_df["equity"].iloc[-1]
  final_return = result_df["cumulative_return"].iloc[-1] - 1
  print(f"\ninitial balance: {INITIAL_BALANCE:,.0f} KRW")
  print(f"final return: {final_return*100:.2f} %")
  print(f"final equity: {final_equity:,.0f} KRW")


