import joblib
import os
import pandas as pd

from src.data_loader          import get_data, patch_last_row_with_realtime
from src.features_engineering import create_features
from src.market_hours         import get_market_status


def scan_market(tickers):
    results = []

    for ticker in tickers:
        try:
            model_path = f"models/{ticker}_model.pkl"
            if not os.path.exists(model_path):
                continue

            saved = joblib.load(model_path)
            mkt   = get_market_status(ticker)

            df        = get_data(ticker)
            df, is_rt = patch_last_row_with_realtime(df, ticker)
            df        = create_features(df)
            df        = df.dropna()
            last      = df.iloc[-1]

            # Umbrales base por horario
            if mkt["status"] == "OPEN":
                base_long, base_short = 0.60, 0.65
            elif mkt["status"] in ("PRE_MARKET", "POST_MARKET"):
                base_long, base_short = 0.65, 0.70
            else:
                base_long, base_short = 0.70, 0.75

            regime      = float(last.get("regime", 0))
            in_downtrend = (
                float(last.get("ma50_slope",   0)) < -0.01
                or float(last.get("drawdown_20d", 0)) < -0.15
            )
            in_uptrend = (
                float(last.get("ma50_slope",  0)) > 0.01
                and float(last.get("drawdown_20d", 0)) > -0.10
            )

            current_price = float(last["Close"])
            prev_close    = float(df["Close"].iloc[-2]) if len(df) > 1 else current_price

            row = {
                "ticker":       ticker,
                "precio":       round(current_price, 4),
                "cambio_%":     round((current_price / prev_close - 1) * 100, 2),
                "rsi":          round(float(last.get("rsi", 0)), 1),
                "regime":       int(regime),
                "drawdown_20d": round(float(last.get("drawdown_20d", 0)) * 100, 1),
                "mercado":      mkt["label"],
                "precio_tipo":  "RT" if is_rt else "Cierre",
                "prob_long":    0.0,
                "prob_short":   0.0,
                "buy":          False,
                "sell":         False,
            }

            # Señal LONG
            if "long" in saved:
                m_long    = saved["long"]["model"]
                feat_long = saved["long"]["features"]
                prob_long = m_long.predict_proba(last[feat_long].to_frame().T)[0][1]
                row["prob_long"] = round(prob_long, 4)

                thr_long = base_long + (0.05 if regime == -1 else 0)
                row["buy"] = (
                    prob_long > thr_long
                    and float(last.get("rsi", 100)) < 68
                    and float(last.get("macd_diff", -1)) > 0
                    and not in_downtrend
                )

            # Señal SHORT
            if "short" in saved:
                m_short    = saved["short"]["model"]
                feat_short = saved["short"]["features"]
                prob_short = m_short.predict_proba(last[feat_short].to_frame().T)[0][1]
                row["prob_short"] = round(prob_short, 4)

                thr_short = base_short + (0.05 if regime == 1 else 0)
                row["sell"] = (
                    prob_short > thr_short
                    and float(last.get("rsi", 0)) > 35
                    and float(last.get("macd_diff", 1)) < 0
                    and not in_uptrend
                )

            results.append(row)

            signal = "✅ BUY" if row["buy"] else ("🔴 SELL" if row["sell"] else "➖")
            print(f"{signal} {ticker:<12} "
                  f"L={row['prob_long']:.3f} S={row['prob_short']:.3f} "
                  f"regime={int(regime):+d} dd={row['drawdown_20d']:.1f}%")

        except Exception as e:
            print(f"❌ {ticker}: {e}")

    return pd.DataFrame(results)
