import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

from src.market_hours import get_market_status, get_asset_type, STOCKS_24_5


def _get_alpaca_keys():
    import os
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
    return os.environ.get("ALPACA_API_KEY", ""), os.environ.get("ALPACA_SECRET_KEY", "")


def _alpaca_latest_price(ticker):
    key, secret = _get_alpaca_keys()
    if not key or not secret:
        return None
    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    url = f"https://data.alpaca.markets/v2/stocks/{ticker}/trades/latest"
    try:
        r = requests.get(url, headers=headers, params={"feed": "delayed_sip"}, timeout=5)
        if r.status_code == 200:
            return float(r.json()["trade"]["p"])
    except Exception as e:
        print(f"⚠️  Alpaca latest price error {ticker}: {e}")
    return None


def _alpaca_intraday(ticker, interval="5m"):
    key, secret = _get_alpaca_keys()
    if not key or not secret:
        return None
    headers = {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}
    interval_map = {"1m":"1Min","2m":"2Min","5m":"5Min","15m":"15Min","30m":"30Min","60m":"1Hour"}
    timeframe = interval_map.get(interval, "5Min")

    from pytz import timezone as tz
    et    = tz("America/New_York")
    now   = datetime.now(et)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    params = {
        "symbols":   ticker,
        "timeframe": timeframe,
        "start":     start.isoformat(),
        "end":       now.isoformat(),
        "feed":      "delayed_sip",
        "limit":     1000,
    }
    try:
        r = requests.get("https://data.alpaca.markets/v2/stocks/bars",
                         headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            return None
        bars = r.json().get("bars", {}).get(ticker, [])
        if not bars:
            return None
        df = pd.DataFrame(bars)
        df = df.rename(columns={"t":"Datetime","o":"Open","h":"High","l":"Low","c":"Close","v":"Volume"})
        df["Datetime"] = pd.to_datetime(df["Datetime"], utc=True).dt.tz_convert(et)
        df = df.set_index("Datetime")[["Open","High","Low","Close","Volume"]]
        return df
    except Exception as e:
        print(f"⚠️  Alpaca intraday error {ticker}: {e}")
    return None


def get_data(ticker):
    """Descarga historial diario para entrenamiento y análisis."""
    period = "max" if "USD" in ticker else "10y"
    df = yf.download(ticker, period=period, interval="1d", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty:
        raise Exception(f"Sin datos para {ticker}")
    return df.dropna()


def get_intraday_data(ticker, interval="5m"):
    """Descarga datos intradía. Para acciones 24/5 usa Alpaca (incluye noche)."""
    asset_type = get_asset_type(ticker)

    if asset_type == "stock_24_5":
        df_alpaca = _alpaca_intraday(ticker, interval)
        if df_alpaca is not None and not df_alpaca.empty:
            return df_alpaca
        print(f"⚠️  Alpaca sin datos para {ticker}, usando yfinance")

    mkt    = get_market_status(ticker)
    period = "1d" if mkt["realtime"] else "5d"
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty:
        raise Exception(f"Sin datos intradía para {ticker}")
    if period == "5d":
        last_day = df.index[-1].date()
        df = df[df.index.date == last_day]
    return df


def get_realtime_price(ticker):
    """
    Obtiene el precio más reciente.
    - Acciones 24/5 → Alpaca (delayed_sip, incluye noche)
    - Crypto / Forex → yfinance
    - Acciones regulares → yfinance (RT en horario, cierre fuera)
    Retorna: (precio, open_price, prev_close, is_realtime)
    """
    asset_type = get_asset_type(ticker)
    mkt        = get_market_status(ticker)

    try:
        if asset_type == "stock_24_5":
            alpaca_price = _alpaca_latest_price(ticker)
            tkr  = yf.Ticker(ticker)
            hist = tkr.history(period="5d", interval="1d")
            open_price = float(hist["Open"].iloc[-1])  if not hist.empty else None
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1  else None
            if alpaca_price is not None:
                return alpaca_price, open_price, prev_close, True
            info    = tkr.fast_info
            current = getattr(info, "last_price", None)
            if current:
                return float(current), open_price, prev_close, mkt["realtime"]

        tkr  = yf.Ticker(ticker)
        info = tkr.fast_info

        if mkt["realtime"]:
            current    = getattr(info, "last_price",     None)
            open_price = getattr(info, "open",           None)
            prev_close = getattr(info, "previous_close", None)
            if current is None:
                intra   = get_intraday_data(ticker, interval="1m")
                current = float(intra["Close"].iloc[-1]) if not intra.empty else None
        else:
            hist       = tkr.history(period="5d", interval="1d")
            current    = float(hist["Close"].iloc[-1]) if not hist.empty else None
            open_price = float(hist["Open"].iloc[-1])  if not hist.empty else None
            prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1  else current

        return (
            float(current)    if current    is not None else None,
            float(open_price) if open_price is not None else None,
            float(prev_close) if prev_close is not None else None,
            mkt["realtime"],
        )
    except Exception as e:
        print(f"⚠️  Error precio {ticker}: {e}")
        return None, None, None, False


def patch_last_row_with_realtime(df, ticker):
    """Sustituye el Close de la última fila con el precio más reciente."""
    current_price, _, _, is_rt = get_realtime_price(ticker)
    if current_price is None:
        return df, False
    df = df.copy()
    df.at[df.index[-1], "Close"] = current_price
    return df, is_rt
