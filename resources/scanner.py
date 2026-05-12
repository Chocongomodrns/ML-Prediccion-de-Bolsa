import joblib
import os
import pandas as pd

from resources.data_loader import get_data
from resources.features_engineering import create_features


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


def scan_market(tickers):

    results = []

    for ticker in tickers:

        try:

            model_path = f"models/{ticker}_model.pkl"

            if not os.path.exists(model_path):
                print(f"⏭️ No model: {ticker}")
                continue

            model = joblib.load(model_path)

            df = get_data(ticker)
            df = create_features(df)
            df = df.dropna()

            last = df.iloc[-1]

            X = last[FEATURES].to_frame().T
            prob = model.predict_proba(X)[0][1]

            threshold = 0.52 if "USD" in ticker else 0.55

            buy = (
                prob > threshold
                and last["Close"] > last["ma50"]
                and last["ma20"] > last["ma50"]
                and last["rsi"] < 70
            )

            results.append({
                "ticker": ticker,
                "prob": prob,
                "buy": buy
            })

            print(f"✅ {ticker}")

        except Exception as e:

            print(f"❌ {ticker}: {e}")

    return pd.DataFrame(results)