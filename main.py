import sys
import os
import yfinance as yf
import pandas as pd
import ta
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

from resources.data_loader import get_data
from resources.features_engineering import create_features
from resources.model_ml import prepare_data, train_model
from resources.strategy import apply_strategy
from resources.scanner import scan_market
from resources.tickers import tickers

df = scan_market(tickers)

# ordenar por probabilidad
df = df.sort_values(by="prob", ascending=False)
df = df.sort_values(by="buy", ascending=False)

crypto_df = df[df['ticker'].str.contains("-USD")]
stocks_df = df[~df['ticker'].str.contains("-USD") & ~df['ticker'].str.contains("=X")]
divisas_df = df[df['ticker'].str.contains("=X")]

print("\n🔥 TOP OPORTUNIDADES DEL DÍA:\n")

print(
"--- CRIPTO ---"
)
print(crypto_df)

print(
"--- ACCIONES ---"
)
print(stocks_df)

print("--- DIVISAS ---")
print(divisas_df)

print("\n🚀 SOLO COMPRAS:\n")

print("--- CRIPTO ---"
)
print(crypto_df[crypto_df['buy'] == True])

print(
"--- ACCIONES ---"
)
print(stocks_df[stocks_df['buy'] == True])

print("--- DIVISAS ---")
print(divisas_df[divisas_df['buy'] == True])

"""def run_model(ticker):
    df = get_data(ticker)
    df = create_features(df)

    features = ['ma20', 'ma50', 'rsi', 'volatility', 'return_1d', 'return_5d']

    df = df.dropna()

    train = df.iloc[:-500]
    test = df.iloc[-500:]

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        class_weight='balanced'
    )

    model.fit(train[features], train['target'])

    test['prob'] = model.predict_proba(test[features])[:,1]

    test['buy'] = (
        (test['prob'] > 0.54) &
        (test['Close'] > test['ma50']) &
        (test['ma20'] > test['ma50']) &
        (test['rsi'] < 70)
    )

    strategy_returns = test[test['buy']]['future_return']

    # stop loss
    strategy_returns = strategy_returns.apply(lambda x: max(x, -0.02))

    print(f"\n=== {ticker} ===")
    print("Trades:", len(strategy_returns))
    print("Return promedio:", strategy_returns.mean())
    print("Win rate:", (strategy_returns > 0).mean())

def get_signal(ticker):
    df = get_data(ticker)
    df = create_features(df)

    df['future_return'] = df['Close'].pct_change().shift(-1)
    df['target'] = (df['future_return'] > 0.008).astype(int)

    df = df.dropna()

    features = ['ma20', 'ma50', 'rsi', 'volatility', 'return_1d', 'return_5d']

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        class_weight='balanced'
    )

    model.fit(df[features], df['target'])

    last = df.iloc[-1]

    prob = model.predict_proba([last[features]])[0][1]

    print(f"\n📊 {ticker}")
    print(f"Probabilidad: {prob}")

    if prob > 0.54 and last['Close'] > last['ma50'] and last['ma20'] > last['ma50']:
        print("🚀 COMPRA")
    else:
        print("❌ NO HACER NADA")

# 1. Descargar datos
df = get_data("NVDA")

# 2. Crear features
df = create_features(df)

# 3. Preparar datos
df = prepare_data(df)

# 4. Features a usar
features = ['return_1d','return_5d','ma20','ma50','rsi','volatility']

# 5. Entrenar modelo
model, train, test = train_model(df, features)

# 6. Aplicar estrategia
test = apply_strategy(model, test, features)

# 7. Evaluación

# Probabilidades
print(test[['prob']].head())

# Métricas
preds = (test['prob'] > 0.5).astype(int)
print(classification_report(test['target'], preds))

# Resultados financieros
strategy_returns = test[test['buy']]['future_return']
# FILTRO (simula stop loss)
strategy_returns = strategy_returns.apply(lambda x: max(x, -0.02))

print("Trades:", len(strategy_returns))
print("Return promedio:", strategy_returns.mean())
print("Win rate:", (strategy_returns > 0).mean())

wins = strategy_returns[strategy_returns > 0]
losses = strategy_returns[strategy_returns <= 0]

print("Ganancia promedio:", wins.mean())
print("Pérdida promedio:", losses.mean())

# Importancia de variables
importance = pd.Series(model.feature_importances_, index=features)
print(importance.sort_values(ascending=False))"""
