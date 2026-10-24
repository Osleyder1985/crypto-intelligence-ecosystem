# Diagnóstico de conectividad para fuentes públicas

Ejecutar desde la raíz del repositorio en el equipo o runner que presenta el fallo:

```bash
python scripts/diagnostics/check_public_source_connectivity.py \
  --timeout-seconds 5 \
  https://www.sec.gov/about/developer-resources \
  https://www.cftc.gov/WebPolicy/index.htm \
  https://www.federalreserve.gov/disclaimer.htm
```

El comando realiza, por URL, una resolución DNS y una petición HTTPS `HEAD` con timeout. No descarga el cuerpo de las páginas, no sigue redirecciones, no cambia DNS/proxy/firewall y no altera autorizaciones de fuentes. El resultado JSON clasifica por separado DNS y HTTPS, registra código HTTP y duración y evita guardar mensajes de error potencialmente sensibles.

Interpretación:
- `dns_status=FAILED`: resolver DNS del entorno no resolvió el host; comprobar DNS, proxy/VPN y conectividad del equipo/runner.
- `dns_status=PASS` y `https_status=FAILED`: investigar TLS, firewall, proxy o timeout.
- `https_status=HTTP_ERROR` con código HTTP: el transporte llegó al servidor, pero el servidor rechazó o no admite HEAD. Eso no demuestra que GET o la captura estén autorizados.
- `PASS`: DNS y petición HTTPS respondieron; no garantiza que una captura histórica ni el endpoint de datos funcionen.

Máximo 20 URLs y timeout entre 0.1 y 30 segundos. La herramienta no repara la red automáticamente: el diagnóstico identifica qué capa debe corregirse. No habilita ninguna fuente del Issue #132.
