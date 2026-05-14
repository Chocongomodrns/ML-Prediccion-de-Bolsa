"""
market_hours.py — Detecta el estado actual de cada tipo de activo.

Estados posibles:
  OPEN        — mercado abierto, precio RT disponible
  PRE_MARKET  — pre-market (4:00–9:30 ET) solo acciones
  POST_MARKET — post-market (16:00–20:00 ET) solo acciones
  CLOSED      — mercado cerrado (noche)
  WEEKEND     — fin de semana

──────────────────────────────────────────────────────────────
  LISTA 24/5 — edita aquí para agregar o quitar tickers
──────────────────────────────────────────────────────────────
Agrega cualquier acción que tu broker opere 24/5.
Se tratarán igual que crypto: siempre OPEN de lunes a viernes,
y WEEKEND solo sábado/domingo.
"""

from datetime import datetime, time
import pytz

ET        = pytz.timezone("America/New_York")
MEXICO_TZ = pytz.timezone("America/Mexico_City")

# ── ✏️  EDITA ESTA LISTA LIBREMENTE ──────────────────────────────────────
STOCKS_24_5 = {
    # Crypto / blockchain
    "MARA", "RIOT", "COIN", "MSTR", "CLSK", "CIFR",
    "HUT",  "BTBT", "WULF", "IREN", "CORZ", "BTDR",
    "IONQ",
    # Añade aquí los que uses:
    # "NVDA", "TSLA",  ...
}
# ─────────────────────────────────────────────────────────────────────────


def _now_et():
    return datetime.now(ET)


def get_asset_type(ticker):
    """Clasifica un ticker: crypto / forex / stock_24_5 / stock."""
    t = ticker.upper().split(".")[0]   # quitar sufijos como .MX

    if t.endswith("-USD") or t.endswith("USDT") or t.endswith("-BTC"):
        return "crypto"
    if t.endswith("=X"):
        return "forex"
    if t in STOCKS_24_5:
        return "stock_24_5"
    return "stock"


# ── Crypto y acciones 24/5 ────────────────────────────────────────────────
def _always_open_status(label_extra=""):
    now    = _now_et()
    weekday = now.weekday()

    if weekday >= 5:
        return {
            "status":   "WEEKEND",
            "label":    "🔴 Cerrado (fin de semana)",
            "realtime": False,
            "message":  f"Reabre el lunes. {label_extra}".strip(),
        }
    return {
        "status":   "OPEN",
        "label":    "🟢 Abierto 24/5",
        "realtime": True,
        "message":  f"Opera sin interrupciones de lunes a viernes. {label_extra}".strip(),
    }


def crypto_status():
    return _always_open_status()


def stock_24_5_status(ticker):
    return _always_open_status(f"({ticker} opera 24/5 en tu broker)")


# ── Forex ─────────────────────────────────────────────────────────────────
def forex_status():
    now     = _now_et()
    weekday = now.weekday()
    t       = now.time()

    if weekday == 5:
        return {
            "status":   "WEEKEND",
            "label":    "🔴 Cerrado (fin de semana)",
            "realtime": False,
            "message":  "Forex cierra el viernes 17:00 ET y reabre el domingo 17:00 ET.",
        }
    if weekday == 6 and t < time(17, 0):
        return {
            "status":   "WEEKEND",
            "label":    "🔴 Cerrado (abre domingo 17:00 ET)",
            "realtime": False,
            "message":  "Forex reabre hoy a las 17:00 ET.",
        }
    if weekday == 4 and t >= time(17, 0):
        return {
            "status":   "WEEKEND",
            "label":    "🔴 Cerrado hasta domingo 17:00 ET",
            "realtime": False,
            "message":  "Forex cerró el viernes a las 17:00 ET.",
        }

    if time(17, 0) <= t or t < time(2, 0):
        session = "Sydney / Tokio"
    elif time(2, 0) <= t < time(8, 0):
        session = "Londres"
    else:
        session = "Nueva York"

    return {
        "status":   "OPEN",
        "label":    f"🟢 Abierto — Sesión {session}",
        "realtime": True,
        "message":  f"Sesión activa: {session}",
    }


# ── Acciones USA (horario regular) ────────────────────────────────────────
def stock_status():
    now     = _now_et()
    weekday = now.weekday()
    t       = now.time()

    if weekday >= 5:
        return {
            "status":   "WEEKEND",
            "label":    "🔴 Cerrado (fin de semana)",
            "realtime": False,
            "message":  "NYSE/NASDAQ abren el lunes 9:30 ET.",
        }
    if time(9, 30) <= t < time(16, 0):
        return {
            "status":   "OPEN",
            "label":    "🟢 Mercado abierto (9:30–16:00 ET)",
            "realtime": True,
            "message":  "NYSE/NASDAQ en sesión regular.",
        }
    if time(4, 0) <= t < time(9, 30):
        return {
            "status":   "PRE_MARKET",
            "label":    "🟡 Pre-market (4:00–9:30 ET)",
            "realtime": True,
            "message":  "Datos disponibles pero liquidez baja. Señales menos confiables.",
        }
    if time(16, 0) <= t < time(20, 0):
        return {
            "status":   "POST_MARKET",
            "label":    "🟡 Post-market (16:00–20:00 ET)",
            "realtime": True,
            "message":  "Datos disponibles pero liquidez baja. Señales menos confiables.",
        }
    return {
        "status":   "CLOSED",
        "label":    "🔴 Cerrado (fuera de horario)",
        "realtime": False,
        "message":  "Mercado cerrado. Se usará el último precio de cierre.",
    }


# ── API pública ───────────────────────────────────────────────────────────
def get_market_status(ticker):
    """
    Retorna el estado del mercado para cualquier ticker.

    Dict devuelto:
      status   : OPEN | PRE_MARKET | POST_MARKET | CLOSED | WEEKEND
      label    : string legible para mostrar en UI
      realtime : bool — True si hay precio RT disponible
      message  : descripción adicional
    """
    asset_type = get_asset_type(ticker)

    if asset_type == "crypto":
        return crypto_status()
    elif asset_type == "forex":
        return forex_status()
    elif asset_type == "stock_24_5":
        return stock_24_5_status(ticker)
    else:
        return stock_status()


def is_realtime_available(ticker):
    """True si el precio RT es confiable para este ticker ahora."""
    return get_market_status(ticker)["realtime"]


def get_local_time_str():
    """Hora actual en México y ET para el dashboard."""
    now_mx = datetime.now(MEXICO_TZ)
    now_et = datetime.now(ET)
    return (
        f"🕐 México: {now_mx.strftime('%H:%M')}  |  "
        f"🗽 Nueva York (ET): {now_et.strftime('%H:%M')}  |  "
        f"📅 {now_et.strftime('%A %d/%m/%Y')}"
    )
