# Pruebas de puerta de frescura en vivo — Issue #18

Estas pruebas ejercitan la función `_live_freshness` con observaciones sintéticas y política explícitamente marcada como aprobada dentro del fixture. Los límites de 0,5 s, 1,0 s y 50 ms **son valores exclusivos de prueba**, no valores recomendados ni política de producto.

Cobertura:
- ausencia de observaciones live y política no aprobada → `INDETERMINATE`;
- timestamp de evento fresco bajo el fixture aprobado → `PASS`;
- timestamp de origen atrasado o snapshot demasiado antiguo → `FAIL`;
- desfase de reloj fuera del límite del fixture → `FAIL`;
- timestamp ausente/futuro y límite mal configurado → `INDETERMINATE`.

La suite comprueba además que el resultado incluya versión y referencia de aprobación de la política. No aprueba la política real, no transforma los nueve deltas observados de Pionex REST en umbrales, no cambia la configuración de producción y no envía órdenes. La política del producto permanece pendiente de una decisión sustentada por más observaciones y análisis de riesgo.
