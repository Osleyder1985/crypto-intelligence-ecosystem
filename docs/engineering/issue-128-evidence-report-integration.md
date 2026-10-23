# Integración de evidencia en el informe E2E — Issue #128

## Estado y alcance

Esta entrega añade una capa de composición offline sobre `crypto-asset-research-report-v2`. Valida e incorpora registros de eventos externos, observaciones fundamentales/on-chain y metodología versionada mediante los contratos existentes de los Issues #132, #134 y #133.

## Entrada

- Informe existente `crypto-asset-research-report-v2`.
- Lista de eventos; cada entrada incluye el evento `crypto-external-event-record-v1`, un identificador estable objetivo y una ventana de movimiento explícita.
- Lista de observaciones `crypto-fundamental-observation-v1`.
- Metodología `crypto-investment-methodology-v1`.
- Identidad estable del activo (ID y categoría) y `evaluation_as_of` con zona horaria.

## Controles

- Valida cada evento, identidad estable y ventana; rechaza IDs de evento duplicados.
- No considera un evento disponible en un corte histórico si su publicación o captura es posterior.
- Evalúa observaciones con el contrato de fundamentales/on-chain; preserva estados ausentes y conflictos, sin rellenar ceros.
- Valida la estructura metodológica, costes y configuración de horizontes.
- Mantiene corto/medio/largo en `INDETERMINATE`, incluso si la metodología figura como APPROVED: la validación contractual no prueba rendimiento predictivo.
- No afirma causalidad, no realiza llamadas de red, no emite órdenes ni aprueba fuentes/licencias.

## Ejecución

```bash
python -m scripts.market_selection.research_evidence_integration \
  --report report.json \
  --events events.json \
  --observations observations.json \
  --methodology methodology.json \
  --asset-stable-id example-asset \
  --asset-category smart_contract_token \
  --evaluation-as-of 2026-10-21T00:00:00Z \
  --output enriched-report.json
```

Los archivos `events.json` y `observations.json` deben ser arrays JSON; `methodology.json` debe cumplir el contrato versionado. Las ventanas de movimiento son inputs explícitos, no inferidos por este módulo.

## Límites pendientes

No hay conectores de red, aprobación de términos, verificación independiente de fuentes, ingestión histórica real ni backtest/modelo predictivo. Los fixtures prueban controles contractuales, no cobertura real, causalidad, calidad de fuentes ni rentabilidad. El informe original debe generarse previamente con el orquestador de #130.


## Integración de soportes y resistencias multi-temporalidad

El informe E2E acepta opcionalmente `research-support-resistance-input-v1` mediante el parámetro `support_resistance_input` (CLI: `--support-resistance-input`). La entrada contiene la identidad estable del activo, una URL de evidencia de mapeo activo-mercado aportada por el llamador, artefactos OHLCV autorizados y parámetros explícitos de pivote/tolerancia. La capa de integración ejecuta el analizador multi-temporal existente y excluye cualquier vela cuyo cierre sea posterior a `evaluation_as_of` antes de detectar pivotes.

El informe conserva zonas, eventos, huecos, calidad, integridad de fuente, parámetros y la cantidad de velas excluidas. El mapeo se etiqueta `CALLER_SUPPLIED_REQUIRES_REVIEW`: la URL no demuestra por sí sola que el par pertenezca al activo solicitado. Si no se suministra la entrada, el estado queda `NOT_AVAILABLE`. Esta integración no modifica `decision_status=INDETERMINATE`, no prueba órdenes resting y no envía órdenes.
