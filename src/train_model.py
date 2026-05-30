"""
Entrena modelos LONG y SHORT por ticker con walk-forward validation.
Ejecutar desde la raíz del proyecto:  py src/train_model.py
"""

import os
import sys
import shutil
import joblib
import pandas as pd
import numpy as np

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics  import classification_report, precision_score
from sklearn.utils.class_weight import compute_sample_weight

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader          import get_data
from src.features_engineering import create_features
from src.market_hours         import get_market_status
from src.tickers              import tickers


FEATURES = [
    "price_vs_ma20", "price_vs_ma50", "price_vs_ma200",
    "ma50_slope", "ma200_slope", "ma_ratio", "regime",
    "drawdown_20d", "drawdown_52w",
    "rsi", "rsi_7", "rsi_21",
    "stoch_rsi_k", "stoch_rsi_d",
    "macd_diff", "macd_diff_slope",
    "return_1d", "return_3d", "return_5d", "return_10d", "return_20d",
    "atr_pct", "bb_pct", "bb_width",
    "vol_ratio", "vol_ratio_5",
]

MIN_PRECISION = 0.28

# Borrar modelos anteriores y empezar limpio
os.makedirs("models", exist_ok=True)
os.makedirs("logs", exist_ok=True)


def walk_forward_score(df, available, target_col, n_splits=3):
    """Walk-forward validation en n_splits ventanas temporales."""
    fold_size  = len(df) // (n_splits + 1)
    precisions = []

    for i in range(1, n_splits + 1):
        train_end  = fold_size * i
        test_start = train_end
        test_end   = test_start + fold_size
        if test_end > len(df):
            break

        train = df.iloc[:train_end]
        test  = df.iloc[test_start:test_end]

        if train[target_col].nunique() < 2 or test[target_col].nunique() < 2:
            continue

        m  = GradientBoostingClassifier(
            n_estimators=100, max_depth=3, learning_rate=0.05,
            subsample=0.8, min_samples_leaf=15, random_state=42,
        )
        sw = compute_sample_weight("balanced", train[target_col])
        m.fit(train[available], train[target_col], sample_weight=sw)

        probs = m.predict_proba(test[available])[:, 1]
        preds = (probs > 0.55).astype(int)
        if preds.sum() > 0:
            precisions.append(precision_score(test[target_col], preds, zero_division=0))

    return np.mean(precisions) if precisions else 0.0


results = []

for ticker in tickers:
    try:
        print(f"\n{'='*50}")
        print(f"Entrenando: {ticker}")

        df = get_data(ticker)

        # Eliminar vela incompleta si el mercado está abierto
        mkt = get_market_status(ticker)
        if mkt["status"] in ("OPEN", "PRE_MARKET", "POST_MARKET"):
            df = df.iloc[:-1]

        df = create_features(df)
        df = df.dropna()

        if len(df) < 400:
            print("❌ Muy pocos datos — omitido")
            continue

        available = [f for f in FEATURES if f in df.columns]
        split     = int(len(df) * 0.85)
        train     = df.iloc[:split]
        test      = df.iloc[split:]
        saved     = {}

        for direction in ["long", "short"]:
            target_col = f"target_{direction}"

            if train[target_col].nunique() < 2:
                print(f"⚠️  {direction.upper()}: sin variación — omitido")
                continue

            wf = walk_forward_score(df, available, target_col, n_splits=3)
            print(f"Walk-forward {direction.upper()}: {wf:.2%}")

            if wf < MIN_PRECISION:
                print(f"⚠️  {direction.upper()}: {wf:.2%} < {MIN_PRECISION:.0%} — omitido")
                continue

            model = GradientBoostingClassifier(
                n_estimators=300, max_depth=4, learning_rate=0.05,
                subsample=0.8, min_samples_leaf=10, random_state=42,
            )
            sw = compute_sample_weight("balanced", train[target_col])
            model.fit(train[available], train[target_col], sample_weight=sw)

            probs = model.predict_proba(test[available])[:, 1]
            preds = (probs > 0.55).astype(int)
            prec  = precision_score(test[target_col], preds, zero_division=0)

            print(classification_report(test[target_col], preds, zero_division=0))
            print(f"Precisión {direction.upper()}: {prec:.2%}")

            if prec < MIN_PRECISION:
                print(f"⚠️  Test {prec:.2%} < {MIN_PRECISION:.0%} — omitido")
                continue

            saved[direction] = {"model": model, "features": available, "precision": prec}
            print(f"✅ Modelo {direction.upper()} listo")

        if saved:
            joblib.dump(saved, f"models/{ticker}_model.pkl")
            print(f"💾 Guardado: models/{ticker}_model.pkl  ({', '.join(saved.keys())})")
            results.append({
                "ticker":     ticker,
                "directions": list(saved.keys()),
                "long_prec":  saved.get("long",  {}).get("precision", 0),
                "short_prec": saved.get("short", {}).get("precision", 0),
                "saved":      True,
            })
        else:
            results.append({"ticker": ticker, "saved": False})

    except Exception as e:
        print(f"❌ {ticker}: {e}")
        import traceback; traceback.print_exc()


print(f"\n{'='*50}")
print("RESUMEN")
df_res = pd.DataFrame(results)
if not df_res.empty:
    saved_df   = df_res[df_res["saved"] == True]
    omitted_df = df_res[df_res["saved"] == False]
    print(f"Guardados: {len(saved_df)}  |  Omitidos: {len(omitted_df)}")
    if len(saved_df):
        print(saved_df[["ticker","directions","long_prec","short_prec"]].to_string())
