import pandas as pd
import numpy as np
import ta


def create_features(df):
    df = df.copy()

    close  = df["Close"].squeeze()
    volume = df["Volume"].squeeze()
    high   = df["High"].squeeze()
    low    = df["Low"].squeeze()

    if isinstance(close, pd.DataFrame):  close  = close.iloc[:, 0]
    if isinstance(volume, pd.DataFrame): volume = volume.iloc[:, 0]
    if isinstance(high, pd.DataFrame):   high   = high.iloc[:, 0]
    if isinstance(low, pd.DataFrame):    low    = low.iloc[:, 0]

    # Retornos
    df["return_1d"]  = close.pct_change()
    df["return_3d"]  = close.pct_change(3)
    df["return_5d"]  = close.pct_change(5)
    df["return_10d"] = close.pct_change(10)
    df["return_20d"] = close.pct_change(20)

    # Medias móviles — NUEVO: agregamos MA200
    df["ma20"]  = close.rolling(20).mean()
    df["ma50"]  = close.rolling(50).mean()
    df["ma200"] = close.rolling(200).mean()

    # NUEVO: posición del precio relativa a cada media (ratio, no valor absoluto)
    # El modelo aprende mejor con ratios que con precios absolutos
    df["price_vs_ma20"]  = (close / df["ma20"])  - 1
    df["price_vs_ma50"]  = (close / df["ma50"])  - 1
    df["price_vs_ma200"] = (close / df["ma200"]) - 1  # negativo = bear market

    # NUEVO: pendiente de las medias (¿está subiendo o bajando la tendencia?)
    df["ma50_slope"]  = df["ma50"].pct_change(5)
    df["ma200_slope"] = df["ma200"].pct_change(10)
    df["ma_ratio"]    = df["ma20"] / df["ma50"]

    # NUEVO: régimen de mercado — el feature más importante que faltaba
    # 1 = alcista (precio > MA50 > MA200)
    # 0 = neutral
    # -1 = bajista (precio < MA50 < MA200)
    df["regime"] = 0
    df.loc[(close > df["ma50"]) & (df["ma50"] > df["ma200"]), "regime"] =  1
    df.loc[(close < df["ma50"]) & (df["ma50"] < df["ma200"]), "regime"] = -1

    # NUEVO: drawdown desde máximos recientes
    # Esto detecta "ya cayó 15%, no entres ahora"
    df["high_20d"]     = high.rolling(20).max()
    df["high_52w"]     = high.rolling(252).max()
    df["drawdown_20d"] = (close / df["high_20d"]) - 1  # siempre <= 0
    df["drawdown_52w"] = (close / df["high_52w"]) - 1

    # RSI en 3 períodos distintos
    df["rsi"]    = ta.momentum.RSIIndicator(close, window=14).rsi()
    df["rsi_7"]  = ta.momentum.RSIIndicator(close, window=7).rsi()
    df["rsi_21"] = ta.momentum.RSIIndicator(close, window=21).rsi()

    # Stochastic RSI
    stoch = ta.momentum.StochRSIIndicator(close)
    df["stoch_rsi_k"] = stoch.stochrsi_k()
    df["stoch_rsi_d"] = stoch.stochrsi_d()

    # MACD
    macd_ind          = ta.trend.MACD(close)
    df["macd"]        = macd_ind.macd()
    df["macd_signal"] = macd_ind.macd_signal()
    df["macd_diff"]   = macd_ind.macd_diff()
    # NUEVO: aceleración del MACD (¿el momentum está aumentando o frenando?)
    df["macd_diff_slope"] = df["macd_diff"].diff(3)

    # Volatilidad
    df["volatility"]    = close.rolling(10).std()
    df["volatility_20"] = close.rolling(20).std()

    atr_ind      = ta.volatility.AverageTrueRange(high, low, close)
    df["atr"]    = atr_ind.average_true_range()
    df["atr_pct"] = df["atr"] / close  # normalizado por precio

    bb = ta.volatility.BollingerBands(close)
    df["bb_width"] = bb.bollinger_wband()
    df["bb_pct"]   = bb.bollinger_pband()

    # Volumen
    df["vol_ratio"]   = volume / volume.rolling(20).mean()
    df["vol_ratio_5"] = volume / volume.rolling(5).mean()

    # TARGET MEJORADO — antes: solo +3% en 3 días
    # Ahora: +3% en 3 días Y sin caer más de 2% en el camino
    # Esto elimina falsos positivos donde sube pero primero cae fuerte
    future_return_3d = (close.shift(-3) / close) - 1

    min_3d = pd.concat([
        low.shift(-1), low.shift(-2), low.shift(-3)
    ], axis=1).min(axis=1)
    no_deep_drop = ((min_3d / close) - 1) >= -0.02

    df["future_return"] = future_return_3d
    df["target"] = ((future_return_3d >= 0.03) & no_deep_drop).astype(int)

    return df