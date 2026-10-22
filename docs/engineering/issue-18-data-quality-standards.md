# Aplicabilidad de normas ISO a frescura de mercado — Issue #18

- **Estado:** nota de aplicabilidad documental; no es una declaración de conformidad/certificación ISO.
- **Issue:** [#18](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/18).
- **Fecha de consulta:** 2026-10-22 UTC.

## Normas verificadas en fuentes oficiales

### ISO 8601-1:2019 — Representación de fechas y horas

Fuente oficial: https://www.iso.org/standard/70907.html

ISO indica que esta edición fue revisada y confirmada en 2024 y permanece vigente. Su alcance es representar fechas, horas, intervalos/desplazamientos y UTC para intercambio de información. Sirve para normalizar timestamps como `2026-10-22T05:00:00.000Z`, pero **no define cuántos milisegundos de antigüedad son aceptables para un libro de órdenes** ni una política de frescura para exchanges.

### ISO/IEC 25012:2008 — Modelo de calidad de datos

Fuente oficial: https://www.iso.org/standard/35736.html

ISO describe esta norma como un modelo general de calidad de datos que puede usarse para establecer requisitos de calidad, definir medidas y planificar/evaluar la calidad. La norma reconoce que la importancia de las características de calidad varía según el contexto y las partes interesadas. No prescribe un límite universal de 100 ms, 500 ms, 1 s u otro para Binance/Pionex Spot.

## Aplicación al ecosistema

1. Conservar el timestamp original, su unidad, semántica y campo de origen.
2. Normalizar la representación temporal a UTC ISO 8601 sin reemplazar el timestamp de origen por la hora local de captura.
3. Medir por separado timestamp de actualización/evento, timestamp de respuesta y captura local; registrar incertidumbre del reloj cuando se comparen relojes distintos.
4. Definir un límite de frescura como requisito de producto/operación basado en mediciones representativas, incertidumbre del reloj y el riesgo de la decisión. No atribuir un umbral numérico a ISO si la norma no lo establece.
5. Evaluar el resultado frente al requisito versionado y aprobado. Si no existe ese requisito, conservar `INDETERMINATE` en vez de inferir `PASS`.

Estas prácticas son una aplicación de las normas consultadas, no una afirmación de que el ecosistema haya sido auditado o certificado conforme a ISO 8601 o ISO/IEC 25012.
