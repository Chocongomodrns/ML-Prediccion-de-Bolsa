"""
market_hours.py — Detecta el estado actual de cada tipo de activo.

Estados posibles:
  OPEN        — mercado abierto, precio RT disponible
  PRE_MARKET  — pre-market (4:00-9:30 ET) solo acciones
  POST_MARKET — post-market (16:00-20:00 ET) solo acciones
  CLOSED      — mercado cerrado (noche)
  WEEKEND     — fin de semana

LISTA 24/5 — edita STOCKS_24_5 para agregar o quitar tickers.
Todos los de eToro S&P500 + Nasdaq100 ya están incluidos.
"""

from datetime import datetime, time
import pytz

ET        = pytz.timezone("America/New_York")
MEXICO_TZ = pytz.timezone("America/Mexico_City")

# ── EDITA ESTA LISTA LIBREMENTE ───────────────────────────────────────────
# eToro ofrece 24/5 para todo el S&P500 y Nasdaq100 desde Nov 2025
STOCKS_24_5 = {
    # Big Tech
    "AAPL","MSFT","GOOGL","GOOG","AMZN","META","NVDA","TSLA","NFLX",
    "ORCL","ADBE","CRM","IBM","CSCO","INTU","AVGO","INTC","AMD","DIS",
    # Semis
    "QCOM","MU","ASML","LRCX","KLAC","TXN","ADI","AMAT","ON","MCHP",
    "SWKS","MRVL","NXPI","TSM","ARM",
    # Software / Cloud
    "PLTR","SNOW","CRWD","ZS","DDOG","SHOP","UBER","LYFT","OKTA","MDB",
    "PANW","FTNT","NOW","TEAM","AXON","WDAY","CDNS","SNPS","NET","TWLO",
    # Fintech / Finance
    "JPM","BAC","GS","MS","V","MA","AXP","COIN","AFRM","SOFI","PYPL",
    "SCHW","BLK","KKR","COF","HOOD","BX","SYF","GPN","UPST",
    # Energía / Industrial
    "XOM","CVX","COP","OXY","BA","CAT","GE","DE","HON","LMT","NOC",
    "RTX","GD","ETN","EMR","PWR","VMC","HAL","SLB",
    # Consumo / Retail
    "COST","WMT","HD","TGT","MCD","SBUX","NKE","LULU","BKNG","ABNB",
    "EXPE","MAR","HLT","LVS","MGM","DKNG","WYNN","RCL","CCL","ORLY",
    # Salud
    "LLY","UNH","JNJ","PFE","ABBV","MRK","BMY","GILD","AMGN","REGN",
    "MRNA","BIIB","VRTX","ISRG","DXCM","NVAX","OCGN",
    # AI / Quantum / Space
    "AI","SOUN","BBAI","IONQ","QBTS","RGTI","QUBT","RKLB","SPCE",
    "APP","CRWV","GEV","TEM",
    # Crypto-related stocks
    "MARA","RIOT","MSTR","CLSK","HUT","IREN","BTBT","WULF","CORZ","CIFR",
    # EVs / Auto
    "RIVN","LCID","NIO","GM","F","PLUG","FSLR",
    # Medios / Entretenimiento
    "RBLX","EA","TTWO","SNAP","PINS","ROKU","TTD","CMCSA","WBD","FOXA","LYV",
    # ETFs
    "SPY","QQQ",
    # Otros S&P500 relevantes
    "AAPL","V","MA","JPM","UNH","COST","HD","PG","KO","PEP","ABBV",
    "ACN","ADSK","AEP","AFL","AIG","AJG","ALB","ALL","ALLE","AME",
    "AMCR","AMD","AMT","AMZN","AON","APD","APH","APO","APTV","ARE",
    "ATO","AVB","AVY","AWK","AXP","AZO","AZN","BAC","BAX","BKNG",
    "BKR","BLK","BLDR","BMY","BR","BRO","BSX","BX","BXP","CAG",
    "CAH","CARR","CB","CBRE","CCL","CDW","CEG","CF","CFG","CHD",
    "CHTR","CI","CINF","CL","CLX","CME","CMI","CMS","CNC","CNP",
    "COF","COO","COP","COR","CPAY","CPB","CPT","CRL","CRDO","CSX",
    "CSGP","CTAS","CTSH","CTVA","CVS","D","DAL","DASH","DD","DE",
    "DECK","DEO","DGX","DHI","DHR","DLR","DLTR","DOC","DOV","DOW",
    "DRI","DTE","DUK","DVA","DVN","DXCM","ECL","ED","EFX","EG",
    "EIX","EL","ELV","EME","EMN","EMR","EOG","EPAM","EQR","EQT",
    "EQIX","ES","ESS","ETR","EVRG","EW","EXC","EXE","EXPD","EXPE",
    "EXR","F","FANG","FAST","FDS","FDX","FE","FICO","FIS","FITB",
    "FRT","FTNT","FTV","GD","GEN","GEHC","GEV","GILD","GIS","GL",
    "GLW","GNRC","GPC","GPN","GS","GWW","HAL","HAS","HBAN","HCA",
    "HD","HIG","HII","HLT","HOLX","HON","HPE","HPQ","HRL","HSIC",
    "HST","HSY","HUM","HWM","ICE","IDXX","IEX","IFF","IQV","IR",
    "IRM","ISRG","IT","ITW","IVZ","J","JBL","JBHT","JCI","JKHY",
    "JNJ","K","KEY","KHC","KIM","KKR","KMB","KMI","KMX","KO","KR",
    "L","LDOS","LEN","LH","LHX","LIN","LKQ","LLY","LMT","LNT","LUV",
    "LVS","LW","LYB","LYV","MA","MAA","MAR","MAS","MCK","MCO","MDLZ",
    "MDT","MET","MHK","MKC","MKTX","MMC","MMM","MNST","MOH","MOS",
    "MPWR","MRK","MRNA","MS","MSCI","MTB","MTD","MTCH","NCLH","NEM",
    "NEE","NI","NKE","NOC","NRG","NSC","NTAP","NTRS","NUE","NVR",
    "NWSA","NWS","O","ODFL","OKE","OMC","OPEN","OTIS","OXY","PAYC",
    "PAYX","PCG","PEG","PFG","PGR","PH","PHM","PKG","PLD","PM",
    "PNC","PODD","POOL","PPG","PPL","PTC","PWR","RF","RJF","RMD",
    "ROK","ROL","ROP","ROST","RSG","RTX","RVTY","SHW","SJM","SLB",
    "SNA","SOLV","SO","SPG","SPGI","SRE","STT","STX","STZ","SW",
    "SWK","SYF","SYK","SYY","T","TAP","TCEL","TDG","TDY","TEL",
    "TEM","TER","TFC","TGT","TJX","TKO","TMO","TMUS","TPL","TPR",
    "TRGP","TRI","TRV","TSCO","TSN","TT","TTWO","TXN","TYL","UAL",
    "UDR","UHS","ULTA","UNP","URI","USB","VLO","VLTO","VTR","VRSN",
    "VRSK","VST","VZ","WAB","WAT","WBD","WEC","WELL","WM","WMB",
    "WTW","WY","XEL","XYL","YUM","ZBH","ZTS",
}
# ─────────────────────────────────────────────────────────────────────────


def _now_et():
    return datetime.now(ET)


def get_asset_type(ticker):
    """Clasifica un ticker: crypto / forex / stock_24_5 / stock."""
    t = ticker.upper().split(".")[0]
    if t.endswith("-USD") or t.endswith("USDT") or t.endswith("-BTC"):
        return "crypto"
    if t.endswith("=X"):
        return "forex"
    if t in STOCKS_24_5:
        return "stock_24_5"
    return "stock"


def _always_open_status(label_extra=""):
    now     = _now_et()
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
    return _always_open_status(f"({ticker} opera 24/5 en eToro)")


def forex_status():
    now     = _now_et()
    weekday = now.weekday()
    t       = now.time()

    if weekday == 5:
        return {"status": "WEEKEND", "label": "🔴 Cerrado (fin de semana)",
                "realtime": False, "message": "Forex cierra el viernes 17:00 ET y reabre el domingo 17:00 ET."}
    if weekday == 6 and t < time(17, 0):
        return {"status": "WEEKEND", "label": "🔴 Cerrado (abre domingo 17:00 ET)",
                "realtime": False, "message": "Forex reabre hoy a las 17:00 ET."}
    if weekday == 4 and t >= time(17, 0):
        return {"status": "WEEKEND", "label": "🔴 Cerrado hasta domingo 17:00 ET",
                "realtime": False, "message": "Forex cerró el viernes a las 17:00 ET."}

    if time(17, 0) <= t or t < time(2, 0):   session = "Sydney / Tokio"
    elif time(2, 0) <= t < time(8, 0):        session = "Londres"
    else:                                      session = "Nueva York"

    return {"status": "OPEN", "label": f"🟢 Abierto — Sesión {session}",
            "realtime": True, "message": f"Sesión activa: {session}"}


def stock_status():
    now     = _now_et()
    weekday = now.weekday()
    t       = now.time()

    if weekday >= 5:
        return {"status": "WEEKEND", "label": "🔴 Cerrado (fin de semana)",
                "realtime": False, "message": "NYSE/NASDAQ abren el lunes 9:30 ET."}
    if time(9, 30) <= t < time(16, 0):
        return {"status": "OPEN", "label": "🟢 Mercado abierto (9:30-16:00 ET)",
                "realtime": True, "message": "NYSE/NASDAQ en sesión regular."}
    if time(4, 0) <= t < time(9, 30):
        return {"status": "PRE_MARKET", "label": "🟡 Pre-market (4:00-9:30 ET)",
                "realtime": True, "message": "Liquidez baja. Señales menos confiables."}
    if time(16, 0) <= t < time(20, 0):
        return {"status": "POST_MARKET", "label": "🟡 Post-market (16:00-20:00 ET)",
                "realtime": True, "message": "Liquidez baja. Señales menos confiables."}
    return {"status": "CLOSED", "label": "🔴 Cerrado (fuera de horario)",
            "realtime": False, "message": "Mercado cerrado. Se usará el último precio de cierre."}


def get_market_status(ticker):
    asset_type = get_asset_type(ticker)
    if asset_type == "crypto":       return crypto_status()
    elif asset_type == "forex":      return forex_status()
    elif asset_type == "stock_24_5": return stock_24_5_status(ticker)
    else:                            return stock_status()


def is_realtime_available(ticker):
    return get_market_status(ticker)["realtime"]


def get_local_time_str():
    now_mx = datetime.now(MEXICO_TZ)
    now_et = datetime.now(ET)
    return (
        f"🕐 México: {now_mx.strftime('%H:%M')}  |  "
        f"🗽 Nueva York (ET): {now_et.strftime('%H:%M')}  |  "
        f"📅 {now_et.strftime('%A %d/%m/%Y')}"
    )
