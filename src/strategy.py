"""
Estrategia de señal con apalancamiento x5.

Con x5 el riesgo real es amplificado: una caída del 2% en el activo
equivale a -10% del capital comprometido. Por eso los filtros son
más estrictos que sin apalancamiento.
"""

LEVERAGE = 5


def apply_strategy(model, test, features):
    test = test.copy()

    # Probabilidad de subida >= 3% en 3 días
    test["prob"] = model.predict_proba(test[features])[:, 1]

    # ── Señal de compra ───────────────────────────────────────────────────
    # Con x5 apalancamiento subimos el umbral de prob y filtramos más
    test["buy"] = (
        (test["prob"]     > 0.57)          # más exigente con x5
        & (test["Close"]  > test["ma50"])  # tendencia alcista
        & (test["ma20"]   > test["ma50"])  # golden cross
        & (test["rsi"]    < 68)            # no sobrecomprado
        & (test["return_1d"] > -0.01)      # sin caída brusca reciente
        & (test["macd_diff"] > 0)          # MACD confirma momentum
    )

    # ── Retorno bruto del activo ──────────────────────────────────────────
    test["raw_return"] = test["future_return"] * test["buy"]

    # ── Retorno con apalancamiento x5 ────────────────────────────────────
    # Stop loss del modelo: -2% en el activo = -10% con x5 → limitamos a -2% activo
    test["strategy_return"] = test["raw_return"].apply(
        lambda r: max(r, -0.02) * LEVERAGE if r != 0 else 0
    )

    return test
