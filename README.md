# Crypto Intelligence Ecosystem

Ecosistema multiplataforma de inteligencia de mercado cripto para **investigación reproducible, comparación de activos y evaluación de oportunidades con gestión explícita del riesgo**.

## Visión del producto

Construir una plataforma de investigación bajo demanda que reúna datos de mercado y otras fuentes verificables en una plataforma central compartida por los clientes web, Android e iOS (y escritorio si los requisitos lo justifican). Cada evaluación debe estar fechada, versionada, trazable, comparable con evaluaciones anteriores y reproducible en la medida que las fuentes permitan.

El sistema debe ayudar a responder, con evidencia y límites explícitos:

- Qué mercados y pares Spot ofrecen datos identificables, comparables y suficiente liquidez visible.
- Cómo cambian las condiciones de un activo a lo largo del tiempo y frente a otros activos.
- Qué movimientos, eventos y factores de mercado coinciden temporalmente con cambios relevantes, separando hechos, correlaciones e hipótesis causales.
- Qué muestran las series históricas, los indicadores, la estructura del libro y las zonas de soporte/resistencia, con validación temporal y advertencias de incertidumbre.
- Qué rankings y evaluaciones son comparables bajo la misma metodología, horizonte y cobertura de datos.

## Principios no negociables

1. **Evidencia antes que afirmaciones:** cada resultado identifica fuente, hora, unidad, metodología, versión y limitaciones.
2. **Reproducibilidad e historial:** las evaluaciones nuevas no sobrescriben las anteriores; cambios de datos y metodología deben poder distinguirse.
3. **Calidad y abstención:** los datos ausentes, ambiguos, incompatibles o temporalmente no verificables se exponen; el sistema puede devolver `INDETERMINATE`.
4. **Costes y riesgo explícitos:** una diferencia de precio o una puntuación no equivale por sí sola a rentabilidad.
5. **Datos comunes:** los clientes consumen contratos de datos y resultados canónicos desde una plataforma central, no reglas de negocio divergentes por dispositivo.
6. **Sin ejecución implícita:** el alcance actual es de investigación pública Spot y evaluación; el envío de órdenes reales requiere una decisión, controles y verificación separados.
7. **Gobernanza honesta:** trazabilidad o alineación documental con normas ISO/IEC no equivale a certificación ni conformidad evaluada externamente.

## Flujo objetivo de evaluación por activo

Al introducir un criptoactivo, el objetivo es generar un expediente histórico con movimientos relevantes y posibles detonantes sustentados por fuentes, zonas de soporte/resistencia y una evaluación explicable para **corto, medio y largo plazo**. Cada horizonte debe exponer escenarios, evidencia a favor/en contra, riesgos, invalidaciones e incertidumbre; la conclusión puede ser favorable, desfavorable o `INDETERMINATE`. La especificación verificable y sus criterios E2E están en [Issue #128](https://github.com/Osleyder1985/crypto-intelligence-ecosystem/issues/128) y [la documentación del flujo](docs/engineering/issue-128-end-to-end-asset-research.md) y [la auditoría de brechas](docs/engineering/issue-128-implementation-gap-audit.md). Esto es el objetivo del producto, no una afirmación de que todas las capacidades estén implementadas.

## Alcance actual de ingeniería

- Captura pública read-only de metadatos, libros Spot y volumen cotizado de 24 horas para un universo de exchanges documentado.
- Validación de identidad de mercado y estructura de libro; preservación de respuestas y hashes.
- Comparación de spread, profundidad visible, VWAP/deslizamiento y tarifas públicas de referencia.
- Evaluación temporal fail-closed: la captura técnica correcta no demuestra por sí sola frescura absoluta.
- Construcción incremental de la metodología de selección de mercados, el catálogo histórico de evaluaciones y los requisitos del motor cuantitativo.

## Límites conocidos

- Una captura puntual no demuestra estabilidad del volumen o de la liquidez.
- La profundidad de una API es la profundidad recibida, no necesariamente el libro completo ni liquidez sostenible.
- Las tarifas públicas no prueban las tarifas efectivas de una cuenta.
- No se afirma rentabilidad, no se envían órdenes reales y no se declara preparación para producción mientras falte evidencia integral.
- Las decisiones de producto y arquitectura pendientes siguen identificadas en los Issues y documentos de ingeniería.

## Cómo se mide el progreso

El avance se declara por requisitos verificables, artefactos reproducibles, pruebas y decisiones registradas; no por cantidad de código, documentos o PR fusionados. La hoja de ruta y la trazabilidad están en [docs/engineering](docs/engineering/README.md).
