import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np

from model.neural_optimizer import IndicatorParamNN
from data_handler import get_data
from indicators import rsi, macd, bollinger_bands
from strategy import generate_signals
from backtester import backtest

"""
convert price data --> model feature(30-day log returns)
"""

def make_features(df, lookback = 30):
  # compute log returns using numpy/pandas for stability
  df = df.copy()
  # log_ret = log(close_t) - log(close_{t-1})
  df["log_ret"] = np.log(df["close"]).diff()
  df = df.dropna()

  # using last N datapoints
  features = df["log_ret"].tail(lookback).tolist()

  # if we don't have enough history, pad with zeros on the left
  if len(features) < lookback:
    pad_len = lookback - len(features)
    features = [0.0] * pad_len + features

  # convert to tensor
  x = torch.tensor(features, dtype = torch.float32).unsqueeze(0) # shape (1,lookback)

  return x

"""Training loop"""

def train_optimizer(
    symbol = "BTC/USDT",
    timeframe = "1h",
    data_length = 200, 
    lr = 0.001,
    epochs = 50
):
  #1) Load Model
  model = IndicatorParamNN()
  optimizer = optim.Adam(model.parameters(), lr = lr)

  #2) Training loop

  for epoch in range(epochs):
    
    #Step 1: Load price data
    df = get_data(symbol, timeframe, data_length)

    #step 2: make feature vector
    x = make_features(df)

    #step 3: Forward pass --> generate indicator parameters
    output = model(x)
    params = model.map_to_params(output)

    #step 4: compute indicators
    df["RSI"] = rsi(df, params["rsi_period"])
    macd_df = macd(df, params["macd_fast"], params["macd_slow"], params["macd_signal"])
    df = df.join(macd_df)
    df = df.join(bollinger_bands(df, window = params["bollinger_bands_window"], num_std = params["bollinger_bands_std"]))

  #step 5: Strategy signal
  # generate_signals returns a Series; assign it into the DataFrame's 'signal' column
  df["signal"] = generate_signals(
    df,
    rsi_period = params["rsi_period"],
    macd_fast = params["macd_fast"],
    macd_slow = params["macd_slow"],
    macd_signal = params["macd_signal"],
    bollinger_bands_window = params["bollinger_bands_window"],
    bollinger_bands_std = params["bollinger_bands_std"]
  )
    
  #step 6: Backtest --> get performance dataframe
  result_df = backtest(df, initial_balance = 1000000, trade_fee = 0.001)
  # derive a scalar reward (use cumulative return at the end)
  final_return = float(result_df["cumulative_return"].iloc[-1] - 1)
  reward_value = torch.tensor(final_return, dtype = torch.float32)

  #step7: loss = -reward (we maximize reward)
  loss = -reward_value
  # Attempt gradient update only if loss is differentiable (this pipeline is non-differentiable
  # because it uses pandas/numpy/backtesting). If it's not, skip optimizer step and warn.
  if isinstance(loss, torch.Tensor) and loss.requires_grad:
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
  else:
    # non-differentiable reward; skip parameter update
    print("Note: reward is non-differentiable in this pipeline; skipping backward/optimizer step.")

  """
  monitoring
  """
  print(f"[Epoch {epoch+1}/{epochs}] Reward: {final_return:.6f}  |  Params: {params}")

print ("Training finished")


###Run directly

if __name__ == "__main__": 
  train_optimizer(epochs = 10)