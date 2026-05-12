import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

from data_loader import get_data
from features_engineering import create_features
from tickers import tickers

# ========= FEATURES =========

FEATURES = [
    "ma20",
    "ma50",
    "rsi",
    "volatility",
    "return_1d",
    "return_3d",
    "return_5d",
    "vol_ratio"
]


# ========= MODELS FOLDER =========

os.makedirs("models", exist_ok=True)


# ========= TRAIN LOOP =========

for ticker in tickers:

    try:

        print(f"\nEntrenando {ticker}...")

        # 1. descargar
        df = get_data(ticker)

        # 2. features
        df = create_features(df)

        # 3. limpiar
        df = df.dropna()

        # evitar tickers con poco historial
        if len(df) < 300:
            print("❌ Muy pocos datos")
            continue


        # 4. split temporal (sin mezclar)
        split = int(len(df) * 0.80)

        train = df.iloc[:split]
        test = df.iloc[split:]


        # 5. modelo
        model = RandomForestClassifier(
            n_estimators=400,
            max_depth=12,
            min_samples_leaf=5,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1
        )


        # 6. fit
        model.fit(
            train[FEATURES],
            train["target"]
        )


        # 7. predicción
        probs = model.predict_proba(
            test[FEATURES]
        )[:, 1]


        preds = (
            probs > 0.50
        ).astype(int)


        # 8. métricas
        print("\nML REPORT:")

        print(
            classification_report(
                test["target"],
                preds,
                zero_division=0
            )
        )


        # 9. guardar
        path = f"models/{ticker}_model.pkl"

        joblib.dump(
            model,
            path
        )

        print(f"✅ Guardado: {ticker}")


        # 10. importancia
        importance = pd.Series(
            model.feature_importances_,
            index=FEATURES
        )

        print("\nFeature importance:")

        print(
            importance
            .sort_values(
                ascending=False
            )
        )


    except Exception as e:

        print(
            f"❌ {ticker}: {e}"
        )