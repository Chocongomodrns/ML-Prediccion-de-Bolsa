import os
import sys
import joblib
import pandas as pd
import numpy as np
import shutil

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics  import classification_report, precision_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from resources.data_loader          import get_data
from resources.features_engineering import create_features
from resources.tickers              import tickers


FEATURES = [
    # Tendencia — los más importantes
    "price_vs_ma20", "price_vs_ma50", "price_vs_ma200",
    "ma50_slope", "ma200_slope", "ma_ratio", "regime",
    # Drawdown
    "drawdown_20d", "drawdown_52w",
    # Momentum
    "rsi", "rsi_7", "rsi_21",
    "stoch_rsi_k", "stoch_rsi_d",
    "macd_diff", "macd_diff_slope",
    # Retornos
    "return_1d", "return_3d", "return_5d", "return_10d", "return_20d",
    # Volatilidad
    "atr_pct", "bb_pct", "bb_width",
    # Volumen
    "vol_ratio", "vol_ratio_5",
]

# Si el modelo no llega al 45% de precisión en walk-forward, no se guarda
# Con x5 apalancamiento, un modelo malo es peor que no tener modelo
MIN_PRECISION = 0.4

if os.path.exists("models"):
    shutil.rmtree("models")
    print("🗑️  Modelos anteriores eliminados")
os.makedirs("models", exist_ok=True)


def walk_forward_score(df, available, n_splits=4):
    """
    Divide el historial en 4 ventanas temporales y mide la precisión
    en cada una. Más realista que un solo split 80/20.

    Ejemplo con n_splits=4 y 2000 filas:
      Fold 1: train[0:400]    → test[400:800]
      Fold 2: train[0:800]    → test[800:1200]
      Fold 3: train[0:1200]   → test[1200:1600]
      Fold 4: train[0:1600]   → test[1600:2000]
    """
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

        if train["target"].nunique() < 2 or test["target"].nunique() < 2:
            continue

        m = GradientBoostingClassifier(
            n_estimators=200, max_depth=4,
            learning_rate=0.05, subsample=0.8,
            min_samples_leaf=10, random_state=42,
        )
        m.fit(train[available], train["target"])

        probs = m.predict_proba(test[available])[:, 1]
        preds = (probs > 0.55).astype(int)

        if preds.sum() > 0:
            p = precision_score(test["target"], preds, zero_division=0)
            precisions.append(p)

    return np.mean(precisions) if precisions else 0.0


results = []

for ticker in tickers:
    try:
        print(f"\n{'='*50}")
        print(f"Entrenando: {ticker}")

        df = get_data(ticker)
        df = create_features(df)
        df = df.dropna()

        if len(df) < 400:
            print("❌ Muy pocos datos — omitido")
            continue

        if df["target"].nunique() < 2:
            print("❌ Target sin variación — omitido")
            continue

        available = [f for f in FEATURES if f in df.columns]

        # Primero validamos — si no pasa el mínimo, no entrenamos el modelo final
        wf_precision = walk_forward_score(df, available)
        print(f"Walk-forward precision: {wf_precision:.2%}")

        if wf_precision < MIN_PRECISION:
            print(f"⚠️  {wf_precision:.2%} < {MIN_PRECISION:.0%} mínimo — omitido")
            results.append({"ticker": ticker, "wf_precision": wf_precision, "saved": False})
            continue

        split = int(len(df) * 0.85)
        train = df.iloc[:split]
        test  = df.iloc[split:]

        # GradientBoosting es más lento que RandomForest pero detecta
        # mejor patrones secuenciales como tendencias bajistas sostenidas
        model = GradientBoostingClassifier(
            n_estimators=300, max_depth=4,
            learning_rate=0.05, subsample=0.8,
            min_samples_leaf=10, random_state=42,
        )
        model.fit(train[available], train["target"])

        probs = model.predict_proba(test[available])[:, 1]
        preds = (probs > 0.55).astype(int)
        prec  = precision_score(test["target"], preds, zero_division=0)

        print(classification_report(test["target"], preds, zero_division=0))
        print(f"Precisión BUY: {prec:.2%}")

        # IMPORTANTE: guardamos el modelo Y la lista de features juntos
        # No guardar si el test final también es malo
        if prec < MIN_PRECISION:
            print(f"⚠️  Test precision {prec:.2%} < {MIN_PRECISION:.0%} — omitido")
            results.append({"ticker": ticker, "wf_precision": wf_precision, "saved": False})
            continue

        joblib.dump({"model": model, "features": available}, f"models/{ticker}_model.pkl")
        print(f"✅ Guardado: models/{ticker}_model.pkl")

        results.append({"ticker": ticker, "wf_precision": wf_precision,
                        "test_precision": prec, "saved": True})

    except Exception as e:
        print(f"❌ {ticker}: {e}")
        import traceback; traceback.print_exc()


print(f"\n{'='*50}")
print("RESUMEN")
df_res = pd.DataFrame(results)
if not df_res.empty:
    saved   = df_res[df_res["saved"] == True]
    omitted = df_res[df_res["saved"] == False]
    print(f"Guardados: {len(saved)}  |  Omitidos: {len(omitted)}")
    if len(saved):
        print(saved.sort_values("wf_precision", ascending=False).head(10).to_string())