# Memoria tecnica (plantilla — 2 a 4 paginas)

> Completar con los datos REALES de la contraparte. Esta plantilla sigue los 6 apartados
> exigidos por el enunciado. Borrar esta linea al entregar.

## 1. Problema y contraparte

- Contraparte real: [nombre, rol, negocio, contacto].
- Problema en sus palabras y en las nuestras.
- Por que esto requiere un agente y no una funcion/hoja de calculo: la decision de
  **agrupar productos equivalentes entre proveedores** y elegir bajo criterios difusos
  (presupuesto vs calidad vs stock) no es regla fija: depende del contexto de cada consulta.
  Un `if` no decide que "Labial SuperStay Matte Ink 5ml" y "SUPERSTAY MATTE INK tono variado"
  son el mismo producto; un LLM con herramientas si, y deja traza de su razonamiento.

## 2. Linea base (cifra medida)

- Como resuelve hoy: [ej. revisa manualmente WhatsApp de distribuidores + paginas de
  tiendas; X minutos por cotizacion; Y cotizaciones/semana; tasa de sobreprecio detectada
  tarde: Z%]. **Medir cronometrando esta semana** antes de construir.
- Metrica declarada: [tiempo por decision de compra] — se re-mide en el apartado 4.

## 3. Decisiones de diseno (con alternativa descartada)

| Decision | Alternativas descartadas | Justificacion |
|---|---|---|
| Ciclo unico con 3 herramientas (no multiagente) | Multiagente (buscador + analista) | El problema cabe en un ciclo; multiagente prohibido por alcance y sin beneficio. |
| Datos existentes (JSON+CSV capturados) | Scraping en vivo de tiendas | Scraping es fragil (bloqueos), viola alcance (recoleccion desde cero / credenciales de terceros) y rompe la demo; los archivos son actualizables por la contraparte. |
| Gemini API compatible OpenAI | gpt-4o-mini (costo), Ollama local (privacidad pero RAM/calidad menor) | Costo cero para demo, latencia baja, mismo codigo cambia de proveedor editando .env. |
| Aritmetica en herramienta `calcular_costo` | Dejar calcular al LLM | Los LLM fallan aritmetica; determinismo auditable. |
| JSON validado con pydantic como contrato | Texto libre/markdown | Render automatico de tabla + export CSV + deteccion de salidas invalidas con correccion guiada. |
| Matching semantico hecho por el LLM | Difusa/regex | Nombres comerciales varian demasiado ("SuperStay", "superstay matte ink", tonos); regex no generaliza y difusa agrupa falsos positivos ("Naked" generico). |

## 4. Resultados contra la linea base

- Repetir la metrica del apartado 2 usando el agente: [X min → Y min].
- Casos de prueba: [n exitos / n fallos documentados] (ver docs/casos_prueba.md).
- Ahorro estimado encontrado en el caso CP-01: mayorista ~$39.000/u vs detal ~$54.700/u.

## 5. Limites y riesgos (que NO debe hacer el agente)

- No transacciona ni paga: solo recomienda; la compra la aprueba la persona.
- No verifica autenticidad de productos: ante publicaciones genericas declara
  `datos_insuficientes` (riesgo de replicas).
- Sus datos caducan con la captura de `data/`; precios cambian (mitigacion: actualizacion
  periodica registrada en `_meta.fecha_captura`).
- Riesgo de sesgo: calificaciones provienen de plataformas; pueden sesgar contra vendedores
  nuevos. Mitigacion: mostrar cifras, no ocultar alternativas.
- Datos personales: no procesar datos de clientes finales; solo consultas de producto.

## 6. Declaracion de uso de IA

| Herramienta/version | Uso | Que corregimos |
|---|---|---|
| [ej. Claude/opencode] | Andamiaje inicial del repositorio, borradores de prompts y docs | Revisamos precios realistas COP, corregimos fila desordenada del CSV, validamos casos de prueba ejecutandolos |
| [LLM usado en el producto] | Es el motor del propio agente | N/A |

- Lo que NO hicimos con IA: [medicion de linea base, entrevista con contraparte, analisis
  final de resultados].
- Cada integrante puede explicar y modificar cualquier parte del sistema.
