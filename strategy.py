import pandas as pd

def generate_signals(
    df,
    rsi_period: int | None = None,
    macd_fast: int | None = None,
    macd_slow: int | None = None,
    macd_signal: int | None = None,
    bollinger_band_window: int | None = None,
    bollinger_bands_std: float | None = None,
):
    """
    지표 기반 매매 신호 생성
    필요한 지표(RSI, MACD, Bollinger)가 없으면 내부에서 계산하여 보장함.
    반환: 매수(+1), 매도(-1), 유지(0) (Series)
    """
    df = df.copy()

    # --- compute missing indicators if needed ---
    try:
        from indicators import rsi, macd, bollinger_bands
    except Exception:
        rsi = macd = bollinger_bands = None

    if 'RSI' not in df.columns and rsi is not None:
        # pass provided period if available
        if rsi_period is not None:
            df['RSI'] = rsi(df, period=int(rsi_period))
        else:
            df['RSI'] = rsi(df)

    # prepare macd_df variable
    macd_df = None
    if (('MACD' not in df.columns or 'MACD_Signal' not in df.columns) and macd is not None):
        # pass provided MACD parameters when available
        macd_kwargs = {}
        if macd_fast is not None:
            macd_kwargs['fast_period'] = int(macd_fast)
        if macd_slow is not None:
            macd_kwargs['slow_period'] = int(macd_slow)
        if macd_signal is not None:
            macd_kwargs['signal_period'] = int(macd_signal)

        if macd_kwargs:
            macd_df = macd(df, **macd_kwargs)
        else:
            macd_df = macd(df)
    # macd() returns DataFrame with 'MACD' and 'MACD_Signal'
    if macd_df is not None and isinstance(macd_df, pd.DataFrame):
        # prefer direct column names if provided
        if 'MACD' in macd_df.columns and 'MACD_Signal' in macd_df.columns:
            df['MACD'] = macd_df['MACD']
            df['MACD_Signal'] = macd_df['MACD_Signal']
        else:
            # fall back to older names if present
            df['MACD'] = macd_df.get('MACD_Line')
            df['MACD_Signal'] = macd_df.get('MACD_Signal_Line')

    # prepare bb_df variable
    bb_df = None
    if (('Bollinger_Upper' not in df.columns or 'Bollinger_Lower' not in df.columns) and bollinger_bands is not None):
        bb_kwargs = {}
        if bollinger_band_window is not None:
            bb_kwargs['window'] = int(bollinger_band_window)
        if bollinger_bands_std is not None:
            bb_kwargs['num_std'] = float(bollinger_bands_std)

        if bb_kwargs:
            bb_df = bollinger_bands(df, **bb_kwargs)
        else:
            bb_df = bollinger_bands(df)
    if bb_df is not None and isinstance(bb_df, pd.DataFrame):
        df['Bollinger_Upper'] = bb_df['Bollinger_Upper']
        df['Bollinger_Lower'] = bb_df['Bollinger_Lower']

    # initial signal set to zero
    df["signal"] = 0

    # RSI-based signals
    if "RSI" in df.columns:
            df.loc[df["RSI"] < 30, "signal"] += 1  # buy
            df.loc[df["RSI"] > 70, "signal"] += -1 # sell

    # MACD-based signals
    if "MACD" in df.columns and "MACD_Signal" in df.columns:
            df.loc[df["MACD"] > df["MACD_Signal"], "signal"] += 1  # buy
            df.loc[df["MACD"] < df["MACD_Signal"], "signal"] += -1 # sell

    # Bollinger bands-based signals
    if "Bollinger_Upper" in df.columns and "Bollinger_Lower" in df.columns:
            df.loc[df["close"] < df["Bollinger_Lower"], "signal"] += 1  # buy
            df.loc[df["close"] > df["Bollinger_Upper"], "signal"] += -1 # sell

    # normalize signals to -1, 0, 1
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
    df["MACD"] = macd_df.get("MACD", macd_df.get("MACD_Line"))
    df["MACD_Signal"] = macd_df.get("MACD_Signal", macd_df.get("MACD_Signal_Line"))
    bb_df = bollinger_bands(df)
    df["Bollinger_Upper"] = bb_df["Bollinger_Upper"]
    df["Bollinger_Lower"] = bb_df["Bollinger_Lower"]

    #신호 생성
    signals = generate_signals(df)
    print(signals.tail(20)) # 마지막 5개 신호 출력

