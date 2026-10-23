# Integración de profundidad visible del libro de órdenes en el informe — Issue #128

- **Módulo:** `scripts/market_selection/attach_order_book_evidence_to_report.py`
- **Pruebas:** `tests/market_selection/test_attach_order_book_evidence_to_report.py`
- **Esquema de apéndice:** `crypto-research-report-order-book-evidence-v1`

## Contrato

El adaptador adjunta al informe existente los análisis descriptivos de snapshots Spot previamente capturados. Cada snapshot debe coincidir exactamente con `requested_asset_id` en formato `exchange:symbol`, tener captura anterior o igual a `evaluation_as_of`, y no duplicar mercado y timestamp dentro del lote. La función exige autorización de uso y persistencia para el informe y para cada proveedor del snapshot. Los bytes de las entradas se preservan mediante SHA-256 en el apéndice.

## Qué contiene

Para cada captura se conservan best bid/ask, spread, cantidades y nominales visibles, desequilibrio descriptivo, niveles por lado, distancia al midpoint y profundidad acumulada. El informe conserva sus conclusiones por horizonte y permanece `INDETERMINATE`; el adaptador no envía órdenes.

## Límites

Una captura representa únicamente la profundidad visible en un instante. Las órdenes pueden cancelarse o modificarse, y no se demuestra liquidez ejecutable, intención, órdenes ocultas ni reacción futura del precio. Una lista vacía queda marcada `NOT_AVAILABLE`, no como un libro sin órdenes. La autorización sintética usada en tests solo prueba el flujo de control y no concede derechos reales.
