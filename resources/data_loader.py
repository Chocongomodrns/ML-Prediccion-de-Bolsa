import yfinance as yf
import pandas as pd


def get_data(ticker):

    # Más historial = mejor para ML
    if "USD" in ticker:
        period = "max"      # cripto
    else:
        period = "10y"      # acciones


    df = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=True,
        progress=False
    )


    # Si yfinance devuelve MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)


    # Validación
    if df.empty:
        raise Exception(f"Sin datos para {ticker}")


    # Limpiar
    df = df.dropna()

    return df