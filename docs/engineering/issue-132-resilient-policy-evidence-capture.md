# Captura resiliente de evidencia de políticas — Issue #132

## Qué hace

`scripts/market_selection/capture_source_policy_evidence.py` recupera únicamente páginas de políticas de SEC, CFTC y Federal Reserve Board. Incorpora:

- reintentos acotados con espera exponencial para errores de conectividad transitorios y HTTP 429/5xx;
- validación HTTPS y restricción de host a los dominios oficiales permitidos;
- lectura del cuerpo hasta EOF, sin límite de tamaño impuesto por la aplicación;
- escritura atómica de los bytes originales en `policy-response.bin`;
- metadatos reproducibles en `policy-evidence.json`: URL solicitada/final, hora UTC, código HTTP, headers no sensibles, intentos, bytes y SHA-256;
- resultado no exitoso y registro de error cuando no se logra recuperar el cuerpo;
- marca explícita `provider_approved: false`: capturar una política no aprueba el proveedor ni autoriza automáticamente almacenamiento de datos de mercado.

## Uso

Ejecutar desde la raíz del repositorio en un entorno con conectividad HTTPS:

```bash
python -m scripts.market_selection.capture_source_policy_evidence \
  --url https://www.sec.gov/about/privacy-information \
  --output-dir artifacts/source-policy-evidence/sec-privacy \
  --user-agent "CryptoIntelligenceResearch/1.0 (contact: operator)"
```

Repetir para las páginas oficiales de CFTC y Federal Reserve Board. El comando devuelve código 0 únicamente si obtiene HTTP 200; ante errores de red/HTTP devuelve código 2 y conserva el expediente de fallo para diagnóstico. No ejecutar URLs de feeds de eventos con esta herramienta.

## Interpretación y límites

- El SHA-256 permite comprobar la integridad de los bytes guardados; no prueba por sí solo la autenticidad legal ni que el análisis de términos sea correcto.
- La lectura hasta EOF no impone un límite local, pero necesita espacio de disco y una respuesta que termine de transmitirse. Los errores no se deben tratar como captura completa.
- Los reintentos no solucionan DNS, proxy, firewall, certificados o conectividad permanentemente rotos; hacen el fallo observable y recuperable cuando es transitorio.
- No se habilitan fuentes ni se cambian los estados `TERMS_PENDING`. El revisor autorizado aún debe definir el alcance por fuente, retención, atribución, terceros y uso permitido.
- No se ejecuta automáticamente un backfill; primero hay que capturar y revisar evidencia de políticas y obtener aprobación de uso documentada.

## Prueba

```bash
python -m unittest tests/market_selection/test_source_policy_evidence_capture.py -v
```

Las pruebas usan respuestas simuladas y no prueban conectividad real. La validación de conectividad real debe ejecutarse en un runner/entorno con salida HTTPS y adjuntar el expediente generado, sin publicar credenciales.
