def apply_strategy(model, test, features):
    test = test.copy()

    # Probabilidad de subida
    test['prob'] = model.predict_proba(test[features])[:,1]

    # Señal de compra
    test['buy'] = ( (test['prob'] > 0.54) &
        (test['Close'] > test['ma50']) &
        (test['rsi'] < 65) &
        (test['return_1d'] > 0)
    )

    # Resultado de la operación
    test['strategy_return'] = test['future_return'] * test['buy']

    return test