import pandas as pd
import ta


def create_features(df):
    df = df.copy()

    close = df['Close'].squeeze()
    volume = df['Volume'].squeeze()

    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    if isinstance(volume, pd.DataFrame):
        volume = volume.iloc[:, 0]

    # retornos
    df["return_1d"] = close.pct_change()
    df["return_3d"] = close.pct_change(3)
    df["return_5d"] = close.pct_change(5)

    df["ma20"] = close.rolling(20).mean()
    df["ma50"] = close.rolling(50).mean()

    df["ma_ratio"] = df["ma20"] / df["ma50"]
    df["price_vs_ma"] = close / df["ma50"]

    df["rsi"] = ta.momentum.RSIIndicator(close).rsi()

    df["volatility"] = close.rolling(10).std()

    df["vol_ratio"] = volume / volume.rolling(20).mean()

    df["future_return"] = (close.shift(-5) / close) - 1

    df['target'] = (df['future_return'] > 0.08).astype(int)


    return df