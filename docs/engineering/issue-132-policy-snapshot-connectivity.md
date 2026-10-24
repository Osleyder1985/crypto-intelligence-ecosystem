# Issue #132 — recuperación de conectividad para evidencia de políticas

## Problema

El entorno interactivo usado durante la revisión no pudo resolver dominios públicos por DNS. Eso impide descargar desde ese entorno los bytes originales de las políticas; no demuestra que SEC, CFTC o Federal Reserve estén caídos.

## Solución operativa

El workflow `.github/workflows/issue-132-policy-snapshots.yml` ejecuta la recuperación desde un runner hospedado de GitHub Actions, separado del entorno interactivo. Captura únicamente páginas oficiales de políticas y estado; no solicita feeds RSS ni artículos, no activa fuentes y no modifica autorizaciones.

El script `scripts/market_selection/capture_source_policy_snapshots.py`:
- usa HTTPS y un User-Agent identificable;
- realiza reintentos acotados para fallos transitorios de red/DNS;
- lee cada respuesta hasta EOF sin imponer un límite local de tamaño;
- registra URL solicitada/final, hora UTC, estado HTTP, tipo de contenido, ETag/Last-Modified, número de bytes y SHA-256 de los bytes exactos;
- guarda los cuerpos originales y un manifiesto como artefacto de Actions con retención de siete días; no los confirma automáticamente en Git.

## Uso del resultado

Un resultado `PASS` confirma que se recuperó una respuesta HTTP 200 y que sus bytes se preservaron en el artefacto; **no constituye aprobación legal ni habilita una fuente**. Un error de DNS, timeout, HTTP distinto de 200 o ausencia de artefacto debe mantenerse como fallo explícito y no convertirse en permiso implícito.

Los estados de SEC, CFTC y Federal Reserve permanecen `TERMS_PENDING` hasta documentar la revisión de alcance, retención y casos de uso. El feed CFTC no se consulta en este workflow, dado que su página oficial informó que los RSS estaban temporalmente deshabilitados en octubre de 2026.

## Validación

El workflow se ejecuta automáticamente en el PR que modifica este capturador y también admite ejecución manual desde Actions. Descargar el artefacto `issue-132-source-policy-snapshots`, revisar `manifest.json` y comprobar que cada `body_sha256` coincide con el archivo indicado antes de usarlo como evidencia.
