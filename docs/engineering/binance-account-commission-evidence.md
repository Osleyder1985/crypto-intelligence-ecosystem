# Captura de evidencia de comisiones Binance Spot por cuenta

- **Estado:** utilidad opcional de evidencia; no es una política aprobada ni una señal de trading.
- **Fuente oficial:** [Binance Spot Commission FAQ](https://github.com/binance/binance-spot-api-docs/blob/master/faqs/commission_faq.md), que documenta `GET /api/v3/account/commission` para consultar las tasas actuales de la cuenta por símbolo.
- **Endpoint:** `GET /api/v3/account/commission?symbol=...` (solicitud firmada, credenciales de cuenta).
- **Script:** `scripts/market_selection/capture_binance_account_commission_evidence.py`.
- **Pruebas offline:** `tests/market_selection/test_capture_binance_account_commission_evidence.py`.

## Uso manual

Desde un entorno donde el usuario esté autorizado a consultar ese endpoint y el servicio oficial sea accesible:

```bash
export BINANCE_API_KEY='...'
export BINANCE_API_SECRET='...'
python scripts/market_selection/capture_binance_account_commission_evidence.py \
  --symbol BTCUSDT \
  --output artifacts/binance-spot-account-commission-evidence-BTCUSDT.json
unset BINANCE_API_KEY BINANCE_API_SECRET
```

Utiliza una API key con los permisos mínimos necesarios para consultar datos de cuenta; no habilites permisos de trading o retiros para esta captura. No introduzcas secretos en el repositorio, línea de comandos, issues, logs ni artefactos. El script no envía órdenes, no usa el endpoint de orden de prueba y no persiste la URL firmada. Los errores HTTP se registran sin guardar su cuerpo.

## Qué valida y qué no

- Preserva el JSON recibido mediante SHA-256 y registra símbolo, hora UTC de consulta y estado de validación.
- Valida que la respuesta corresponda al símbolo solicitado y contenga tasas maker/taker/buyer/seller en los grupos standard, tax y special, junto con los metadatos de descuento.
- `commission_evidence_status=PASS` significa que la respuesta de la cuenta pasó la validación estructural en el momento de consulta. **No** significa que se haya aprobado la política del Issue #18 ni que el coste total de una orden esté calculado.
- El cálculo final aún debe determinar el tipo de orden (maker/taker), el lado, los componentes de comisión aplicables, descuentos y activo de cobro, el tamaño de orden requerido por el producto, la profundidad disponible y cualquier otro coste material.
- Si el endpoint devuelve error, falta un campo o el esquema no coincide, el estado queda `INDETERMINATE`; no se inventa una tarifa cero.
- Este endpoint requiere autenticación de cuenta. Una ejecución desde GitHub Actions o una región restringida puede no estar autorizada o no ser accesible. No usar proxies ni intentar eludir restricciones regionales; ejecutar solo desde un entorno permitido. Si no se dispone de evidencia de tarifa efectiva para Pionex u otro proveedor, sus comisiones permanecen `INDETERMINATE`.

## Fuente y límite normativo

La documentación oficial de Binance explica que las tasas pueden incluir componentes standard, tax y special, y descuentos por cuenta/símbolo. No se asigna una tasa universal ni se afirma que ISO establezca una tasa de comisión o un plazo universal de vigencia. La evidencia es una observación fechada y debe revalidarse antes de usarse en una evaluación posterior.
