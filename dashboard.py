import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from resources.scanner import scan_market
from resources.data_loader import get_data
from resources.features_engineering import create_features
from resources.tickers import tickers

if "scan_df" not in st.session_state:
    st.session_state.scan_df = None

st.set_page_config(
    page_title="ML Trading Dashboard",
    layout="wide"
)

st.title("🚀 ML Trading Dashboard")

# boton escaneo
if st.button("Escanear mercado"):

    with st.spinner("Escaneando..."):
        df = scan_market(tickers)

        df = df.sort_values(
            "prob",
            ascending=False
        )

        st.session_state.scan_df = df

    if len(df) == 0:
        st.error("No se encontraron datos")
        st.stop()

    if st.session_state.scan_df is not None:

        df = st.session_state.scan_df

        st.success("Escaneo completado")

    df = df.sort_values("prob", ascending=False)

# boton reset
if st.button("Reset"):
    st.session_state.scan_df = None
    st.rerun()

# dashboard persistente
if st.session_state.scan_df is not None:
    df = st.session_state.scan_df
    st.success("Escaneo completado")
    
    # ======================
    # METRICAS
    # ======================

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Tickers",
        len(df)
    )

    c2.metric(
        "Compras",
        df["buy"].sum()
    )

    c3.metric(
        "Prob promedio",
        round(df["prob"].mean(), 2)
    )

    c4.metric(
        "Mejor setup",
        df.iloc[0]["ticker"]
    )

    # ======================
    # FILTROS
    # ======================

    st.sidebar.title("Filtros")

    only_buys = st.sidebar.checkbox(
        "Solo compras"
    )

    asset_type = st.sidebar.selectbox(
        "Tipo",
        [
            "Todos",
            "Crypto",
            "Stocks"
        ]
    )


    filtered = df.copy()


    if only_buys:
        filtered = filtered[
            filtered["buy"] == True
        ]


    if asset_type == "Crypto":
        filtered = filtered[
            filtered["ticker"].str.contains("-USD")
        ]


    if asset_type == "Stocks":
        filtered = filtered[
            ~filtered["ticker"].str.contains("-USD")
        ]


    # ======================
    # TABLA
    # ======================

    st.dataframe(
        filtered,
        use_container_width=True
    )


    # ======================
    # GRAFICA
    # ======================

    selected = st.selectbox(
        "Selecciona ticker",
        filtered["ticker"]
    )


    chart_df = get_data(selected)
    chart_df = create_features(chart_df)


    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3]
    )


    # PRECIO
    fig.add_trace(
        go.Scatter(
            x=chart_df.index,
            y=chart_df["Close"],
            name="Precio"
        ),
        row=1,
        col=1
    )


    # MA20
    fig.add_trace(
        go.Scatter(
            x=chart_df.index,
            y=chart_df["ma20"],
            name="MA20"
        ),
        row=1,
        col=1
    )


    # MA50
    fig.add_trace(
        go.Scatter(
            x=chart_df.index,
            y=chart_df["ma50"],
            name="MA50"
        ),
        row=1,
        col=1
    )


    # RSI
    fig.add_trace(
        go.Scatter(
            x=chart_df.index,
            y=chart_df["rsi"],
            name="RSI"
        ),
        row=2,
        col=1
    )


    fig.update_layout(
        height=700
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

