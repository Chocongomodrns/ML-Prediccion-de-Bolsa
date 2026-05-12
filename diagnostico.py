import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import joblib
import pandas as pd
import numpy as np
from resources.data_loader import get_data
from resources.features_engineering import create_features

FEATURES = [
    "ma20", "ma50", "rsi", "volatility",
    "return_1d", "return_3d", "return_5d",
    "vol_ratio", "macd_diff", "bb_pct", "atr",
]

for ticker in ["MARA", "AI"]:
    print(f"\n{'='*50}")
    print(f"DIAGNÓSTICO: {ticker}")
    print("="*50)

    try:
        model = joblib.load(f"models/{ticker}_model.pkl")
        df    = get_data(ticker)
        df    = create_features(df)
        df    = df.dropna()

        split     = int(len(df) * 0.80)
        train     = df.iloc[:split]
        test      = df.iloc[split:]
        available = [f for f in FEATURES if f in df.columns]

        # ── Métricas en test ──────────────────────────────────────────────
        probs     = model.predict_proba(test[available])[:, 1]
        preds_55  = (probs > 0.55).astype(int)
        preds_60  = (probs > 0.60).astype(int)

        for thresh, preds in [(0.55, preds_55), (0.60, preds_60)]:
            total    = preds.sum()
            wins     = ((preds == 1) & (test["target"] == 1)).sum()
            false_p  = ((preds == 1) & (test["target"] == 0)).sum()
            prec     = wins / (total + 1e-9)
            print(f"\nUmbral {thresh}: señales={total}  correctas={wins}  falsas={false_p}  precisión={prec:.2%}")

        # ── Distribución del target ───────────────────────────────────────
        print(f"\nTarget en TRAIN: {train['target'].value_counts().to_dict()}")
        print(f"Target en TEST:  {test['target'].value_counts().to_dict()}")

        # ── Últimas 10 filas: prob vs lo que realmente pasó ───────────────
        last10      = df.iloc[-13:-3].copy()   # últimas 10 con target conocido
        last10_prob = model.predict_proba(last10[available])[:, 1]
        last10["prob"]   = last10_prob
        last10["signal"] = (last10_prob > 0.55).astype(int)

        print(f"\nÚltimos 10 días (target ya conocido):")
        print(last10[["Close", "rsi", "ma20", "ma50", "prob", "signal", "target", "future_return"]].to_string())

        # ── Señal actual ──────────────────────────────────────────────────
        last        = df.iloc[[-1]]
        current_prob = model.predict_proba(last[available])[0][1]
        print(f"\nPROB ACTUAL: {current_prob:.4f}")
        print(f"Close:  {float(last['Close'].iloc[0]):.4f}")
        print(f"MA20:   {float(last['ma20'].iloc[0]):.4f}")
        print(f"MA50:   {float(last['ma50'].iloc[0]):.4f}")
        print(f"RSI:    {float(last['rsi'].iloc[0]):.2f}")
        print(f"MACD diff: {float(last['macd_diff'].iloc[0]):.4f}")

        # ── Feature importance ────────────────────────────────────────────
        importance = pd.Series(
            model.feature_importances_, index=available
        ).sort_values(ascending=False)
        print(f"\nFeature importance:")
        print(importance.to_string())

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
