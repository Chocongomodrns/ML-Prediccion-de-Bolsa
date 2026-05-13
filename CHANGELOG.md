# Changelog — ML Trading Dashboard

## v2.1.0 — 2026-05-13
### Added
- Señales SHORT (-3% en 3 días) además de LONG
- Reestructura de directorios: src/, tools/, models/, logs/
- Lista 24/5 expandida con todo el S&P500 y Nasdaq100 de eToro
- sample_weight balanceado en entrenamiento (fix clases desbalanceadas)
- MA200 en gráfica histórica
- Alerta de frescura del escaneo en dashboard

### Changed
- Todos los módulos movidos de resources/ a src/
- Scripts de Git movidos a tools/
- calculoIngresos.py movido a tools/

## v2.0.0 — 2026-05-11
### Added
- Dashboard 24/5 con horarios por tipo de activo
- Precio en tiempo real via Alpaca (delayed_sip)
- Gráfica intradía con VWAP
- Walk-forward validation
- Features de régimen y drawdown
- GradientBoosting en lugar de RandomForest
