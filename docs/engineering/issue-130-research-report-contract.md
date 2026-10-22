# Informe integrado de investigación — contrato inicial de Issue #130

- **Estado:** primer contrato técnico propuesto; no es una recomendación de inversión ni el cierre de Issue #128.
- **Implementación:** `scripts/market_selection/research_report.py`, `scripts/market_selection/canonical_asset_identity.py`.
- **Pruebas:** `tests/market_selection/test_research_report.py`, `tests/market_selection/test_canonical_asset_identity.py`.
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

El CLI es offline: no descarga datos ni busca noticias. Recibe un artefacto histórico, configuración y, si existe, evidencia canónica revisada. No busca por sí mismo nombres/tickers ni sustituye la futura API/interfaz; sin evidencia de identidad, el resultado permanece parcial.

## Reglas conservadoras

1. No se infiere el activo base concatenando/partiendo un símbolo como `BTCUSDT`. La coincidencia entre el ticker solicitado y `market.base_asset` solo puede verificar `market_base_asset_mapping_status`; **no verifica identidad canónica**. Sin evidencia canónica única, revisada y vinculada al símbolo base, `canonical_asset_identity_status=NOT_RESOLVED` y `asset_identity_status=INDETERMINATE`. Si el símbolo de mercado contradice el activo solicitado o la evidencia, la ejecución falla.
2. La evidencia canónica usa `crypto-canonical-asset-identity-v1` e incluye `stable_id`, tipo de activo, símbolo/nombre, cadena, contrato cuando aplique, estado de resolución (`VERIFIED_UNIQUE`), `candidate_count=1`, revisión aprobada y una fuente HTTPS con SHA-256. Para `TOKEN` y `WRAPPED_ASSET`, cadena y dirección de contrato son obligatorias; una dirección solicitada también exige `chain_id`.
3. El resolver no consulta registries ni inventa equivalencias. Valida el contrato y la coincidencia exacta; el hash verifica la integridad del contenido referenciado, no su autoridad. La fuente y la unicidad deben ser revisadas por una persona.
2. Se preserva SHA-256 y número de bytes del archivo exacto en la ejecución CLI. Las llamadas en memoria usan hash de serialización JSON canónica y lo declaran.
3. Los parámetros de detección de movimientos y soporte/resistencia son obligatorios en una configuración versionada; no se introducen umbrales ocultos.
4. Los tres horizontes se emiten por separado, pero permanecen `INDETERMINATE` hasta aprobar metodologías específicas y añadir cobertura de eventos, fundamentales y on-chain.
5. La causa de los movimientos se marca no disponible; el detector OHLCV no es un motor de noticias ni prueba causalidad.
6. No hay ranking, probabilidad predictiva, rentabilidad esperada, órdenes reales ni credenciales de trading.

## Uso

Para intentar resolver identidad canónica, proporciona un archivo `crypto-canonical-asset-identity-v1` revisado mediante `--identity-evidence` y declara el tipo del identificador con `--asset-id-type`. Sin esa evidencia, el informe permanece parcial aunque el ticker coincida con `base_asset`.


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
