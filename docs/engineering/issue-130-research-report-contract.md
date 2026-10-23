# Informe integrado de investigación — contrato inicial de Issue #130

- **Estado:** primer contrato técnico propuesto; no es una recomendación de inversión ni el cierre de Issue #128.
- **Implementación:** `scripts/market_selection/research_report.py`, `scripts/market_selection/canonical_asset_identity.py` y `scripts/market_selection/capture_binance_spot_research.py` (captura de solo lectura más composición del informe).
- **Configuración de ejemplo:** `configs/technical-descriptive-baseline.json` (experimental; sus parámetros no están aprobados como señal de inversión).
- **Pruebas:** `tests/market_selection/test_research_report.py`, `tests/market_selection/test_canonical_asset_identity.py`.
- **Schema de salida:** `crypto-asset-research-report-v2`.
- **Entrada:** artefacto preservado `binance-spot-ohlcv-capture-v1` y archivo de configuración de metodología con parámetros explícitos.

## Qué integra

El orquestador reutiliza los analizadores existentes para generar un único artefacto JSON que contiene:
- perfil descriptivo de riesgo OHLCV;
- eventos descriptivos de retorno/volumen;
- zonas de soporte y resistencia;
- hashes/tamaño del artefacto fuente, identidad del activo y calidad;
- resultados separados para `short`, `medium` y `long`;
- limitaciones, estados y causas de abstención.

`research_report.py` es offline: no descarga datos ni busca noticias. Recibe un artefacto histórico, configuración y, si existe, evidencia canónica revisada. Por separado, `capture_binance_spot_research.py` ya implementa una secuencia de solo lectura que captura `exchangeInfo` para un símbolo nativo exacto, obtiene velas OHLCV y llama al generador de informes. No resuelve por sí mismo un nombre/ticker ambiguo ni sustituye una futura API/interfaz.

La captura en vivo está sometida al control `provider_license_gate`: `live_technical_test` permite una prueba técnica, pero no habilita el análisis interno. Para generar un informe desde una captura en vivo, `internal_analysis` exige un registro de autorización válido para ese proveedor y uso; la disponibilidad pública de un endpoint no demuestra por sí sola una licencia. No se debe inventar ni reutilizar una autorización sintética como permiso real. La identidad canónica también requiere evidencia única, revisada y vinculada al activo base. Si falta cualquiera de estas condiciones, el flujo debe bloquearse o entregar un informe parcial/indeterminado, nunca eludir el control.

## Resolución de candidatos de mercado — incremento técnico

El módulo `scripts/market_selection/resolve_binance_spot_market_candidates.py` permite filtrar un artefacto completo de `exchangeInfo` por símbolo nativo o ticker base y, opcionalmente, por activo cotizado. Solo considera mercados en estado `TRADING` con `isSpotTradingAllowed=true`. Devuelve todos los candidatos ordenados de forma determinista y distingue `UNIQUE_MARKET`, `AMBIGUOUS_MARKET` y `NO_MARKET`; no elige arbitrariamente un par cuando hay varios.

La captura de `exchangeInfo` solicita ahora la respuesta completa sin parámetro de símbolo y la preserva íntegra en Base64, con tamaño y SHA-256, hasta EOF. El símbolo exacto se selecciona localmente después de validar el cuerpo. No se introduce un límite local de bytes. Los límites y fallos del proveedor o del entorno deben reflejarse como fallos de captura, no como truncamiento silencioso.

**Límite explícito:** esta mejora resuelve candidatos de mercado, no nombres de activos ni identidad canónica entre cadenas. Un ticker como `BTC` puede devolver varios pares y requiere un filtro de cotización o una decisión explícita; el estado de candidato único tampoco sustituye evidencia de identidad revisada ni autorización para el uso previsto de los datos.

## Reglas conservadoras

1. No se infiere el activo base concatenando/partiendo un símbolo como `BTCUSDT`. La coincidencia entre el ticker solicitado y `market.base_asset` solo puede verificar `market_base_asset_mapping_status`; **no verifica identidad canónica**. Sin evidencia canónica única, revisada y vinculada al símbolo base, `canonical_asset_identity_status=NOT_RESOLVED` y `asset_identity_status=INDETERMINATE`. Si el símbolo de mercado contradice el activo solicitado o la evidencia, la ejecución falla.
2. La evidencia canónica usa `crypto-canonical-asset-identity-v1` e incluye `stable_id`, tipo de activo, símbolo/nombre, cadena, contrato cuando aplique, estado de resolución (`VERIFIED_UNIQUE`), `candidate_count=1`, revisión aprobada y una fuente HTTPS con `content_base64` y SHA-256 coincidente. Para `TOKEN` y `WRAPPED_ASSET`, cadena y dirección de contrato son obligatorias; una dirección solicitada también exige `chain_id`.
3. El resolver no consulta registries ni inventa equivalencias. Recalcula el hash sobre `content_base64` y el hash del registro de identidad, pero no descarga la URL ni demuestra por sí mismo que el dominio sea oficial o que el contenido otorgue derechos. La fuente, su autoridad y la unicidad deben ser revisadas por una persona.
2. Se preserva SHA-256 y número de bytes del archivo exacto en la ejecución CLI. Las llamadas en memoria usan hash de serialización JSON canónica y lo declaran.
3. Los parámetros de detección de movimientos y soporte/resistencia son obligatorios en una configuración versionada; no se introducen umbrales ocultos.
4. Los tres horizontes se emiten por separado, pero permanecen `INDETERMINATE` hasta aprobar metodologías específicas y añadir cobertura de eventos, fundamentales y on-chain.
5. La causa de los movimientos se marca no disponible; el detector OHLCV no es un motor de noticias ni prueba causalidad.
6. No hay ranking, probabilidad predictiva, rentabilidad esperada, órdenes reales ni credenciales de trading.

## Uso

Para intentar resolver identidad canónica, proporciona un archivo `crypto-canonical-asset-identity-v1` revisado mediante `--identity-evidence` y declara el tipo del identificador con `--asset-id-type`. Sin esa evidencia, el informe permanece parcial aunque el ticker coincida con `base_asset`.

## Captura y evaluación integrada desde Binance Spot

Con los requisitos de autorización y de identidad ya satisfechos mediante evidencias reales revisadas, el flujo integrado se invoca así:

```bash
python -m scripts.market_selection.capture_binance_spot_research \
  --symbol BTCUSDT \
  --base-asset-ticker BTC \
  --interval 1h \
  --start-time-ms <START_TIME_MS_INCLUSIVE> \
  --end-time-ms <END_TIME_MS_EXCLUSIVE> \
  --config configs/technical-descriptive-baseline.json \
  --authorization-record artifacts/reviewed-binance-authorization.json \
  --identity-evidence artifacts/reviewed-canonical-identity.json \
  --capture-output artifacts/binance-spot-ohlcv-capture.json \
  --report-output artifacts/crypto-asset-research-report.json
```

Los dos tiempos son límites UTC en milisegundos Unix; el inicio es inclusivo y el final exclusivo. El símbolo debe ser el símbolo nativo exacto de Binance Spot y `--base-asset-ticker` debe coincidir con el `baseAsset` recibido. El ejemplo no significa que los archivos de autorización o identidad ya existan o estén aprobados: deben contener evidencia real, revisada y aplicable. Sin autorización válida para `internal_analysis`, la ejecución falla antes de solicitar metadatos; una autorización de prueba técnica no basta.

La configuración incluida hace reproducible un experimento descriptivo, no define horizontes temporales aprobados, no genera probabilidades predictivas ni valida rentabilidad. No debe describirse como estrategia de inversión aprobada. Los horizontes se mantienen `INDETERMINATE` mientras falten las metodologías y evidencias requeridas.


```bash
python -m scripts.market_selection.research_report \
  --asset-id BTC \
  --identity-evidence artifacts/reviewed-canonical-identity.json \
  --artifact artifacts/binance-spot-ohlcv-capture.json \
  --config configs/technical-descriptive-baseline.json \
  --output artifacts/crypto-asset-research-report.json
```

El archivo de configuración debe contener `methodology_id`, `methodology_version`, `movement.lookback_bars`, `movement.return_threshold_pct`, `movement.volume_ratio_threshold`, `support_resistance.pivot_left`, `support_resistance.pivot_right` y `support_resistance.tolerance_bps`. Los valores son parámetros del experimento, no umbrales de inversión aprobados.

## Limitaciones pendientes

- El generador offline no captura ni selecciona por sí mismo las fuentes históricas; el capturador integrado actual cubre solamente metadatos de mercado y OHLCV de Binance Spot.
- No ingiere noticias, anuncios, regulación ni eventos on-chain.
- No tiene metodología de horizontes aprobada y no emite tesis de inversión.
- No hay persistencia central, API, UI, autenticación ni multiusuario.
- La prueba E2E inicial es offline y cubre la composición de módulos; no demuestra un producto desplegado ni preparación para producción.
