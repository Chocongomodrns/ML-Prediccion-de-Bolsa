# ML Trading Dashboard

Predicción de movimientos de acciones, crypto y forex con ML.
Apalancamiento x5 · LONG +2.5% / SHORT -3% en 3 días.

## Estructura
```
TradingML/
├── src/          ← módulos del motor ML
├── models/       ← modelos entrenados (.pkl) — no se suben a Git
├── logs/         ← logs de entrenamiento
├── tools/        ← scripts de utilidad
├── dashboard.py  ← interfaz Streamlit
└── .env          ← API keys (no se sube a Git)
```

## Setup inicial
```bat
pip install -r requirements.txt
copy .env.example .env
:: Edita .env con tus keys de Alpaca
```

## Uso
```bat
:: Entrenar modelos
py src/train_model.py

:: Lanzar dashboard
streamlit run dashboard.py
```

## Reentrenamiento
Cada domingo automáticamente si configuraste la tarea programada.
O manualmente: `py src/train_model.py`
