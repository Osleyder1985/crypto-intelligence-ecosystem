# Informe integrado de investigación — contrato inicial de Issue #130

- **Estado:** primer contrato técnico propuesto; no es una recomendación de inversión ni el cierre de Issue #128.
- **Implementación:** `scripts/market_selection/research_report.py`.
- **Pruebas:** `tests/market_selection/test_research_report.py`.
- **Schema de salida:** `crypto-asset-research-report-v1`.
- **Entrada:** artefacto preservado `binance-spot-ohlcv-capture-v1` y archivo de configuración de metodología con parámetros explícitos.

## Qué integra

El orquestador reutiliza los analizadores existentes para generar un único artefacto JSON que contiene:
- perfil descriptivo de riesgo OHLCV;
- eventos descriptivos de retorno/volumen;
- zonas de soporte y resistencia;
- hashes/tamaño del artefacto fuente, identidad del activo y calidad;
- resultados separados para `short`, `medium` y `long`;
- limitaciones, estados y causas de abstención.

El CLI es offline: no descarga datos ni busca noticias. Recibe un artefacto histórico ya capturado y un archivo de configuración; por eso todavía no resuelve por sí mismo un nombre/ticker arbitrario ni sustituye la futura API/interfaz.

## Reglas conservadoras

1. No se infiere el activo base concatenando/partiendo un símbolo como `BTCUSDT`. Si el artefacto no incluye `base_asset` o `asset_id`, la identidad queda `INDETERMINATE`; si contradice el activo solicitado, la ejecución falla.
2. Se preserva SHA-256 y número de bytes del archivo exacto en la ejecución CLI. Las llamadas en memoria usan hash de serialización JSON canónica y lo declaran.
3. Los parámetros de detección de movimientos y soporte/resistencia son obligatorios en una configuración versionada; no se introducen umbrales ocultos.
4. Los tres horizontes se emiten por separado, pero permanecen `INDETERMINATE` hasta aprobar metodologías específicas y añadir cobertura de eventos, fundamentales y on-chain.
5. La causa de los movimientos se marca no disponible; el detector OHLCV no es un motor de noticias ni prueba causalidad.
6. No hay ranking, probabilidad predictiva, rentabilidad esperada, órdenes reales ni credenciales de trading.

## Uso

```bash
python -m scripts.market_selection.research_report \
  --asset-id BTC \
  --artifact artifacts/binance-spot-ohlcv-capture.json \
  --config configs/technical-descriptive-baseline.json \
  --output artifacts/crypto-asset-research-report.json
```

El archivo de configuración debe contener `methodology_id`, `methodology_version`, `movement.lookback_bars`, `movement.return_threshold_pct`, `movement.volume_ratio_threshold`, `support_resistance.pivot_left`, `support_resistance.pivot_right` y `support_resistance.tolerance_bps`. Los valores son parámetros del experimento, no umbrales de inversión aprobados.

## Limitaciones pendientes

- No captura ni selecciona por sí mismo las fuentes históricas.
- No ingiere noticias, anuncios, regulación ni eventos on-chain.
- No tiene metodología de horizontes aprobada y no emite tesis de inversión.
- No hay persistencia central, API, UI, autenticación ni multiusuario.
- La prueba E2E inicial es offline y cubre la composición de módulos; no demuestra un producto desplegado ni preparación para producción.
