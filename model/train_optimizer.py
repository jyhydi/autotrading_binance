import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd

from neural_optimizer import IndicatorParamNN
from data_handler import get_data
from indicators import rsi, macd, bollinger_bands
from strategy import generate_signals
from backtester import backtest

"""
convert price data --> model feature(30-day log returns)
"""

def make_features(df, lookback = 30):
  df["log_return"] = (df["close"] / df["close"].shift(1).apply(lambda x : torch.log(torch.tensor(x))))
  df = df.dropna()

  # using last N datas
  features = df["log_ret"].tail(lookback).tolist()

  #convert to tensor

  x = torch.tensor(features, dtype = torch.float32).unsqueeze(0) # shape (1,30)

  return x

"""Training loop"""

def train_optimizer(
    symbol = "BTC/USDT",
    timeframe = "1h",
    data_length = "200", 
    lr = 0.001,
    epochs = 50
):
  #1) Load Model
  model = IndicatorParamNN()
  optimizer = optim.Adam(model.parameters(), lr = lr)

  #2) Training loop

  for epoch in range(epochs):
    
    #Step 1: Load price data
    df = get_data(symbol, timeframe, data_len)

    #step 2: make feature vector
    x = make_features(df)

    #step 3: Forward pass --> generate indicator parameters
    output = model(x)
    params = model.map_to_params(output)

    #step 4: compute indicators
    df["RSI"] = rsi(df, params["rsi_period"])
    macd_df = macd(df, params["macd_fast"], params["macd_slow"], params["macd_signal"])
    df = df.join(macd_df)
    df = df.join(bollinger_bands(df, window = params["bollinger_band_window"], num_std = params["bollinger_bands_std"]))

    #step 5: Strategy signal
    df = generate_signals(df, 
                          rsi_period = params["rsi_period"],
                          macd_fast = params["macd_fast"],
                          macd_slow = params["macd_slow"],
                          macd_signal = params["macd_signal"]
                          )
    
    #step 6: Backtest --> reward(profit)
    reward = backtest(df, initial_balance = 1000000, trade_fee = 0.001)
    reward_value = torch.tensor(reward, dtype = torch.float32)

    #step7: loss = -reward(maximize reward)
    loss = -reward_value
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    """
    monitoring
    """
    print(f"[Epoch {epoch+1}/{epochs}] Reward: {reward:.2f}  |  Params: {params}")

print ("Training finished")


###Run directly

if __name__ == "__main__": 
  train_optimizer(epochs = 10)