# Evidencia de comisiones Pionex Spot a partir de fills

- **Utilidad:** `scripts/market_selection/capture_pionex_fill_fee_evidence.py`
- **Endpoint de solo lectura:** `GET /api/v1/trade/fills`
- **Fuente oficial:** [Pionex Trade API — Get fills](https://www.pionex.com/docs/api-docs/trade-api/trade) y [Authentication](https://www.pionex.com/docs/api-docs/trade-api/general-info/authentication).
- **Permiso requerido:** lectura de cuenta; no habilitar permisos de trading ni transferencia.
- **Alcance:** evidencia histórica de fills; no es una consulta de tarifa prospectiva equivalente a `GET /api/v3/account/commission` de Binance.

## Ejecución local

Usa una API key dedicada de Pionex con permiso de lectura. No pegues secretos en chat, issues, código ni logs. El script solo llama al host fijo `https://api.pionex.com`, no incluye operaciones de orden y no persiste los identificadores de fill/orden ni el cuerpo privado de la respuesta.

```bash
set +x
read -r -s -p "Pionex API key: " PIONEX_API_KEY; printf '\\n'
read -r -s -p "Pionex API secret: " PIONEX_API_SECRET; printf '\\n'
export PIONEX_API_KEY PIONEX_API_SECRET
python scripts/market_selection/capture_pionex_fill_fee_evidence.py \\
  --symbol BTC_USDT --quote-currency USDT \\
  --start-ms 1792540800000 --end-ms 1792627200000 \\
  --output artifacts/pionex-fill-fee-evidence-BTC_USDT.json
unset PIONEX_API_KEY PIONEX_API_SECRET
```

Sustituye el intervalo por el periodo histórico que realmente quieras analizar; los tiempos son milisegundos Unix. La captura no ejecuta órdenes.

## Cómo interpretar

- La API documenta `fee`, `feeCoin`, `price`, `size`, `role`, `side` y timestamp del fill.
- Si `feeCoin` coincide con el activo cotizado, calcula `fee / (price × size)` por fill. Si la comisión se cobró en otro activo, no convierte ni inventa un tipo de cambio: deja esa tasa como `INDETERMINATE`.
- La documentación indica que el endpoint devuelve los últimos 100 fills cuando se supera el máximo; una respuesta de 100 registros se marca como potencialmente truncada y no se presenta como muestra completa.
- El artefacto conserva SHA-256 y bytes de la respuesta original, pero omite su contenido sin filtrar e identificadores de fill/orden para reducir exposición de historial privado.
- Los fills históricos permiten observar comisión efectivamente cobrada en esas operaciones. No demuestran por sí solos la tarifa vigente para nuevas órdenes, descuentos actuales, ni costes de retiro/red.
