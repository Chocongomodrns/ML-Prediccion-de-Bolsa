import joblib
import os
import pandas as pd

from resources.data_loader          import get_data, patch_last_row_with_realtime
from resources.features_engineering import create_features
from resources.market_hours         import get_market_status


def scan_market(tickers):
    results = []

    for ticker in tickers:
        try:
            model_path = f"models/{ticker}_model.pkl"
            if not os.path.exists(model_path):
                continue

            # El .pkl ahora guarda un dict con modelo + features
            saved     = joblib.load(model_path)
            model     = saved["model"]
            available = saved["features"]

            mkt       = get_market_status(ticker)
            df        = get_data(ticker)
            df, is_rt = patch_last_row_with_realtime(df, ticker)
            df        = create_features(df)
            df        = df.dropna()
            last      = df.iloc[-1]

            prob = model.predict_proba(last[available].to_frame().T)[0][1]

            # Umbral base según horario del mercado
            if mkt["status"] == "OPEN":
                threshold = 0.65
            elif mkt["status"] in ("PRE_MARKET", "POST_MARKET"):
                threshold = 0.70
            else:
                threshold = 0.75

            # Si el régimen es bajista, subimos el umbral 5% más
            # Esto es lo que evitaba que MARA y AI siguieran dando BUY en caída
            regime = float(last.get("regime", 0))
            if regime == -1:
                threshold += 0.05

            # Filtros de tendencia — bloquea señal si está en downtrend activo
            in_downtrend = (
                float(last.get("ma50_slope", 0))   < -0.01   # MA50 bajando >1% en 5 días
                or float(last.get("drawdown_20d", 0)) < -0.15  # caída >15% desde máximo 20d
            )

            buy = (
                prob > threshold
                and float(last.get("price_vs_ma50", -1)) > -0.05  # no muy por debajo MA50
                and float(last.get("rsi", 100)) < 68
                and float(last.get("macd_diff", -1)) > 0
                and not in_downtrend
            )

            current_price = float(last["Close"])
            prev_close    = float(df["Close"].iloc[-2]) if len(df) > 1 else current_price

            results.append({
                "ticker":       ticker,
                "precio":       round(current_price, 4),
                "cambio_%":     round((current_price / prev_close - 1) * 100, 2),
                "prob":         round(prob, 4),
                "rsi":          round(float(last.get("rsi", 0)), 1),
                "regime":       int(regime),
                "drawdown_20d": round(float(last.get("drawdown_20d", 0)) * 100, 1),
                "buy":          buy,
                "mercado":      mkt["label"],
                "precio_tipo":  "RT" if is_rt else "Cierre",
            })

            print(f"{'✅ BUY' if buy else '➖'} {ticker:<12} "
                  f"precio={current_price:.3f}  prob={prob:.3f}  "
                  f"regime={int(regime):+d}  dd={float(last.get('drawdown_20d',0))*100:.1f}%")

        except Exception as e:
            print(f"❌ {ticker}: {e}")

    return pd.DataFrame(results)