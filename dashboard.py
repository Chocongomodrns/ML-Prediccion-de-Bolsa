import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from src.scanner              import scan_market
from src.data_loader          import get_data, get_intraday_data, get_realtime_price
from src.features_engineering import create_features
from src.market_hours         import get_market_status, get_local_time_str
from src.tickers              import tickers

st.set_page_config(page_title="ML Trading Dashboard", page_icon="🚀", layout="wide")
st.title("🚀 ML Trading Dashboard")
st.caption(get_local_time_str())
st.caption("Apalancamiento x5 · LONG +2.5% / SHORT -3% en 3 días")

# Estado de mercados
with st.expander("🌍 Estado de mercados ahora", expanded=True):
    col_s, col_f, col_c = st.columns(3)
    stock_s  = get_market_status("AAPL")
    forex_s  = get_market_status("EURUSD=X")
    crypto_s = get_market_status("BTC-USD")
    col_s.metric("📈 Acciones USA", stock_s["label"])
    col_f.metric("💱 Forex",        forex_s["label"])
    col_c.metric("₿  Crypto",       crypto_s["label"])
    col_s.caption(stock_s["message"])
    col_f.caption(forex_s["message"])
    col_c.caption(crypto_s["message"])

# Sesión
if "scan_df"   not in st.session_state: st.session_state.scan_df   = None
if "scan_time" not in st.session_state: st.session_state.scan_time = None

# Sidebar
st.sidebar.title("⚙️ Filtros")
signal_filter = st.sidebar.selectbox("Señal", ["Todas", "Solo BUY", "Solo SELL"])
asset_type    = st.sidebar.selectbox("Activo", ["Todos", "Crypto", "Stocks", "Forex"])
min_prob      = st.sidebar.slider("Prob mínima", 0.50, 0.95, 0.55, 0.01)
only_open     = st.sidebar.checkbox("Solo mercados abiertos")
st.sidebar.markdown("---")
st.sidebar.markdown("💡 **x5**: prob > 0.65 y RSI < 60 para LONG\n\n📉 **SHORT**: prob > 0.65 y RSI > 60")

# Botones
col_btn1, col_btn2, _ = st.columns([1, 1, 6])
with col_btn1:
    scan_clicked = st.button("🔍 Escanear mercado", use_container_width=True)
with col_btn2:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.scan_df   = None
        st.session_state.scan_time = None
        st.rerun()

if scan_clicked:
    with st.spinner("Escaneando mercado…"):
        df = scan_market(tickers)
        df = df.sort_values("prob_long", ascending=False)
        st.session_state.scan_df   = df
        st.session_state.scan_time = datetime.now()

# Dashboard
if st.session_state.scan_df is not None:
    df = st.session_state.scan_df

    # Alerta de frescura
    if st.session_state.scan_time:
        mins = int((datetime.now() - st.session_state.scan_time).total_seconds() // 60)
        if mins < 2:     st.success(f"✅ Escaneo hace {mins} min — precios vigentes")
        elif mins < 10:  st.warning(f"⚠️ Escaneo hace {mins} min — precios pueden haber cambiado")
        else:            st.error(f"🔴 Escaneo hace {mins} min — re-escanea antes de operar con x5")

    # Filtros
    filtered = df.copy()
    if signal_filter == "Solo BUY":  filtered = filtered[filtered["buy"]  == True]
    if signal_filter == "Solo SELL": filtered = filtered[filtered["sell"] == True]
    if asset_type == "Crypto":   filtered = filtered[filtered["ticker"].str.contains("-USD")]
    elif asset_type == "Stocks": filtered = filtered[~filtered["ticker"].str.contains("-USD") & ~filtered["ticker"].str.contains("=X")]
    elif asset_type == "Forex":  filtered = filtered[filtered["ticker"].str.contains("=X")]
    filtered = filtered[
        (filtered["prob_long"] >= min_prob) | (filtered["prob_short"] >= min_prob)
    ]
    if only_open: filtered = filtered[filtered["mercado"].str.contains("🟢")]

    # ======================
    # EVITAR SEÑALES FALSAS
    # ======================

    if len(filtered) > 0:

        # LONG que ya explotó
        if "buy" in filtered.columns:

            filtered.loc[
                (
                    (filtered["buy"] == True)
                    &
                    (filtered["cambio_%"] > 1.8)
                ),
                "buy"
            ] = False


            filtered.loc[
                (
                    (filtered["prob_long"] > 0.75)
                    &
                    (filtered["cambio_%"] > 1.8)
                ),
                "buy_status"
            ] = "🟢 HOLD"


        # SHORT que ya cayó
        if "sell" in filtered.columns:

            filtered.loc[
                (
                    (filtered["sell"] == True)
                    &
                    (filtered["cambio_%"] < -2.0)
                ),
                "sell"
            ] = False


            filtered.loc[
                (
                    (filtered["prob_short"] > 0.75)
                    &
                    (filtered["cambio_%"] < -2.0)
                ),
                "sell_status"
            ] = "🔴 HOLD"

    # Métricas
    st.markdown("### 📊 Resumen")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Tickers",        len(df))
    c2.metric("Señales BUY",    int(df["buy"].sum())  if "buy"  in df.columns else 0)
    c3.metric("Señales SELL",   int(df["sell"].sum()) if "sell" in df.columns else 0)
    best = df.loc[df["prob_long"].idxmax()] if len(df) else None
    c4.metric("Mejor LONG",  best["ticker"]       if best is not None else "—")
    c5.metric("Mejor prob",  f"{best['prob_long']:.2%}" if best is not None else "—")

    # Tabla
    st.markdown("### 📋 Resultados")

    def style_row(row):
        if row.get("buy"):  return ["background-color: #1a3a1a"] * len(row)
        if row.get("sell"): return ["background-color: #3a1a1a"] * len(row)
        if "🔴" in str(row.get("mercado", "")): return ["opacity: 0.6"] * len(row)
        return [""] * len(row)

    display_cols = [
        "ticker",
        "precio",
        "precio_tipo",
        "cambio_%",
        "prob_long",
        "prob_short",
        "buy",
        "buy_status",
        "sell",
        "sell_status",
        "rsi",
        "regime",
        "drawdown_20d",
        "mercado"
    ]
    available_cols = [c for c in display_cols if c in filtered.columns]

    st.dataframe(
        filtered[available_cols].style.apply(style_row, axis=1),
        use_container_width=True, height=300,
    )

    # Análisis de ticker
    st.markdown("---")
    st.markdown("### 📈 Análisis de ticker")

    ticker_options = filtered["ticker"].tolist() if len(filtered) else df["ticker"].tolist()
    col_sel, col_tf = st.columns([3, 1])
    with col_sel:
        selected = st.selectbox("Selecciona un ticker", ticker_options)
    with col_tf:
        timeframe = st.selectbox("Período", ["1 mes","3 meses","6 meses","1 año","2 años","5 años"], index=1)

    tf_map = {"1 mes":30,"3 meses":90,"6 meses":180,"1 año":365,"2 años":730,"5 años":1825}
    days_back = tf_map[timeframe]

    mkt_status = get_market_status(selected)
    st.info(f"{mkt_status['label']}  —  {mkt_status['message']}")

    rt_price, rt_open, rt_prev, is_rt = get_realtime_price(selected)

    if rt_price:
        pct = (rt_price / rt_prev - 1) * 100 if rt_prev else 0
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(f"{'💰 Precio RT' if is_rt else '🔒 Último cierre'}", f"{rt_price:,.4f}", delta=f"{pct:+.2f}%")
        m2.metric("📂 Apertura",        f"{rt_open:,.4f}" if rt_open else "—")
        m3.metric("🔒 Cierre anterior", f"{rt_prev:,.4f}" if rt_prev else "—")
        m4.metric("⚡ Tipo de dato",    "Tiempo real" if is_rt else "Último cierre")

    tab_hist, tab_1d = st.tabs(["📅 Histórico", "⚡ Hoy (intradía)"])

    # TAB Histórico
    with tab_hist:
        chart_df = get_data(selected)
        chart_df = create_features(chart_df)
        chart_df = chart_df.iloc[-days_back:]
        if rt_price and is_rt:
            chart_df.at[chart_df.index[-1], "Close"] = rt_price

        fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                            vertical_spacing=0.04, row_heights=[0.60, 0.20, 0.20],
                            subplot_titles=("Precio + MAs", "RSI", "MACD"))

        fig.add_trace(go.Candlestick(
            x=chart_df.index, open=chart_df["Open"], high=chart_df["High"],
            low=chart_df["Low"], close=chart_df["Close"], name="Precio",
            increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        ), row=1, col=1)
        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["ma20"], name="MA20",
                                  line=dict(color="#ffa726", width=1.2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["ma50"], name="MA50",
                                  line=dict(color="#42a5f5", width=1.2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["ma200"], name="MA200",
                                  line=dict(color="#ab47bc", width=1.2)), row=1, col=1)
        if rt_price and is_rt:
            fig.add_trace(go.Scatter(x=[chart_df.index[-1]], y=[rt_price], mode="markers",
                                      name="Precio RT", marker=dict(color="#ff4081", size=10, symbol="diamond")), row=1, col=1)

        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["rsi"], name="RSI",
                                  line=dict(color="#ab47bc", width=1.2)), row=2, col=1)
        for level, color in [(70, "red"), (30, "green")]:
            fig.add_hline(y=level, line_dash="dash", line_color=color, opacity=0.4, row=2, col=1)

        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["macd"], name="MACD",
                                  line=dict(color="#66bb6a", width=1)), row=3, col=1)
        fig.add_trace(go.Scatter(x=chart_df.index, y=chart_df["macd_signal"], name="Señal",
                                  line=dict(color="#ef5350", width=1)), row=3, col=1)
        fig.add_trace(go.Bar(x=chart_df.index, y=chart_df["macd_diff"], name="Histograma",
                              marker_color=chart_df["macd_diff"].apply(
                                  lambda v: "#26a69a" if v >= 0 else "#ef5350")), row=3, col=1)

        fig.update_layout(height=750, template="plotly_dark", showlegend=True,
                           xaxis_rangeslider_visible=False,
                           title=dict(text=f"{selected} — {timeframe}", font=dict(size=16)))
        st.plotly_chart(fig, use_container_width=True)

    # TAB Intradía
    with tab_1d:
        if mkt_status["status"] in ("CLOSED", "WEEKEND"):
            st.warning(f"⚠️ {mkt_status['label']} — Mostrando el último día hábil disponible.")
        elif mkt_status["status"] in ("PRE_MARKET", "POST_MARKET"):
            st.warning(f"⚠️ {mkt_status['label']} — Liquidez baja, spreads amplios. Opera con precaución x5.")

        intraday_interval = st.radio("Intervalo", ["1m","2m","5m","15m","30m"], index=2, horizontal=True)

        try:
            intra = get_intraday_data(selected, interval=intraday_interval)
            if intra.empty:
                st.warning("No hay datos intradía disponibles.")
            else:
                fig2 = make_subplots(rows=2, cols=1, shared_xaxes=True,
                                     vertical_spacing=0.05, row_heights=[0.70, 0.30],
                                     subplot_titles=("Precio intradía", "Volumen"))

                fig2.add_trace(go.Candlestick(
                    x=intra.index, open=intra["Open"], high=intra["High"],
                    low=intra["Low"], close=intra["Close"], name="Precio",
                    increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
                ), row=1, col=1)

                if "Volume" in intra.columns and intra["Volume"].sum() > 0:
                    tp   = (intra["High"] + intra["Low"] + intra["Close"]) / 3
                    vwap = (tp * intra["Volume"]).cumsum() / intra["Volume"].cumsum()
                    fig2.add_trace(go.Scatter(x=intra.index, y=vwap, name="VWAP",
                                               line=dict(color="#ffeb3b", width=1.5, dash="dot")), row=1, col=1)

                if rt_price and is_rt:
                    fig2.add_hline(y=rt_price, line_dash="dash", line_color="#ff4081",
                                   annotation_text=f"RT {rt_price:,.4f}",
                                   annotation_position="right", row=1, col=1)

                bar_colors = ["#26a69a" if c >= o else "#ef5350"
                              for o, c in zip(intra["Open"], intra["Close"])]
                fig2.add_trace(go.Bar(x=intra.index, y=intra["Volume"], name="Volumen",
                                       marker_color=bar_colors, opacity=0.7), row=2, col=1)

                fig2.update_layout(height=600, template="plotly_dark",
                                   xaxis_rangeslider_visible=False,
                                   title=dict(text=f"{selected} — 1 día ({intraday_interval})"
                                              + ("" if is_rt else " [último día hábil]"),
                                              font=dict(size=16)))
                st.plotly_chart(fig2, use_container_width=True)

                d1, d2, d3, d4 = st.columns(4)
                d1.metric("Apertura",    f"{float(intra['Open'].iloc[0]):,.4f}")
                d2.metric("Máximo",      f"{float(intra['High'].max()):,.4f}")
                d3.metric("Mínimo",      f"{float(intra['Low'].min()):,.4f}")
                d4.metric("Últ. precio", f"{float(intra['Close'].iloc[-1]):,.4f}")

        except Exception as e:
            st.error(f"Error al cargar datos intradía: {e}")

else:
    st.info("👆 Pulsa **Escanear mercado** para comenzar.")
