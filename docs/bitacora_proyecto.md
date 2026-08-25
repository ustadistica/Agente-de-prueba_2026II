# Bitácora del proyecto — Agente Belleza CO

Documento de trabajo del equipo. Su propósito: **dejar evidencia verificable del progreso
y de la ejecución del agente**, en el formato que la rúbrica puede auditar. Se diligencia
al final de cada sesión de trabajo (5–10 minutos) y se versiona en el repositorio.

> Las entradas marcadas **[referencia]** corresponden al prototipo construido como material
> de la actividad; el grupo debe generar sus propias entradas reemplazándolas o
> complementándolas.

---

## 1. Cómo diligenciarla

- Una entrada por sesión de trabajo, con fecha e integrantes presentes.
- Campos obligatorios: **hicimos / decidimos / evidencia**. Los demás si aplican.
- "Decidimos" siempre incluye la alternativa descartada en una línea (alimenta directo la
  memoria técnica y la sustentación).
- "Evidencia" debe ser verificable: hash de commit, nombre de test, `id` de la bitácora de
  ejecución, o URL.

```
### AAAA-MM-DD · [integrantes]
- Hicimos: ...
- Decidimos: ... (alternativa descartada: ...)
- Evidencia: commit <hash> · test <nombre> · bitácora ids <id,...>
- Dificultades: ...
- IA usada: herramienta y para qué; qué corregimos manualmente.
```

---

## 2. Hitos de la actividad (checklist de avance)

Mapeados a la rúbrica. Marcar con la evidencia correspondiente.

| # | Hito | Semana | Criterio | Estado | Evidencia |
|---|------|--------|----------|--------|-----------|
| 1 | Dos contrapartes contactadas por correo | 1 | C1.0 | ☐ | |
| 2 | Reunión de 20 min con la contraparte | 1 | C1.0 | ☐ | |
| 3 | Línea base medida (cronometrada) | 1 | C1.2 | ☐ | |
| 4 | Visto bueno del caso (media página) | 1 | C1 | ☐ | |
| 5 | Constancia del encargo diligenciada | 1 | entregable | ☐ | `docs/constancia_encargo_plantilla.md` |
| 6 | Algo que corre (aunque corra mal) | 2 | C3 | ☐ | |
| 7 | Prompts v1 guardados y documentados | 2 | C3.2 | ☐ | `prompts/sistema_v1.txt` |
| 8 | Errores gestionados por tipo | 2 | C3.3 | ☐ | Tabla 2 del informe técnico |
| 9 | Casos de prueba ejecutados con registro (incluye ≥1 fallo) | 3 | C4.1 | ☐ | `docs/casos_prueba.md` + bitácora |
| 10 | Resultados vs línea base con la MISMA métrica | 3 | C4.2 | ☐ | sección 4 de abajo |
| 11 | Memoria técnica (2–4 págs) | 3 | entregable | ☐ | plantilla en `docs/` |
| 12 | Instrucciones para la contraparte | 3 | C4.5 | ☐ | `docs/instrucciones_contraparte.md` |
| 13 | Ensayo de sustentación cronometrado (≤10 min) | 3 | C5.5 | ☐ | |
| 14 | Arranque del entorno en <60 s verificado | 3 | C3 | ☐ | |

---

## 3. Registro de línea base y resultados (C1.2 / C4.2)

Métrica declarada: **tiempo por decisión de compra** (mínutos). Medir la misma métrica
antes y después; reportar ambas con su procedimiento.

| Medición | Fecha | Procedimiento | Tiempo (min) | Observaciones |
|----------|-------|---------------|--------------|----------------|
| Línea base (manual) | | cronometrar cotización real con la contraparte | | |
| Con el agente (misma tarea) | | misma consulta, mismo producto | | |

---

## 4. Entradas de trabajo

### 2026-08-25 · [referencia] Construcción del prototipo
- Hicimos: datasets (26 refs retail + 18 distribuidor), ciclo del agente con 3
  herramientas, contrato de salida con pydantic, interfaz Streamlit con filtros, 2 tests
  del bucle con LLM simulado.
- Decidimos: datos existentes editables en vez de scraping en vivo (alternativa
  descartada: scraping — fragilidad y permisos de terceros).
- Evidencia: commit `228c16a` · tests `test_bucle_stub.py` 2/2 OK.
- IA usada: andamiaje de código con IA bajo supervisión; corrección manual de una fila
  desordenada del CSV detectada en verificación.

### 2026-08-25 · [referencia] Auditoría de calidad y correcciones
- Hicimos: revisión de 5 ejes (corrección, legibilidad, arquitectura, seguridad,
  rendimiento). Hallazgos: crash ante CSV malformado (corregido), recomendación de ID
  inexistente sin validar (corregido con validación cruzada), estados de casos de prueba
  sobreestimados (relabelados honestamente).
- Decidimos: validar cada fila del CSV con mensaje que identifica fila y columna
  (alternativa descartada: try/except genérico — esconde el dato que hay que corregir).
- Evidencia: tests ampliados a 4/4 OK (`test_bucle_stub.py`) · commit posterior.

### 2026-08-25 · [referencia] Despliegue e informe técnico
- Hicimos: soporte de credenciales vía `st.secrets` para Streamlit Community Cloud,
  informe técnico LaTeX de 7 páginas (justificación, objetivos, construcción,
  funcionamiento), publicación de todo en el repositorio.
- Decidimos: `config.py` lee `.env` o `st.secrets` (alternativa descartada: solo
  variables de entorno — obligaba a configurar el entorno también en la nube).
- Evidencia: commits `efab75a`, `c8731ec` · `docs/informe_tecnico/`.

### 2026-08-25 · [referencia] Bitácora de ejecución automática
- Hicimos: registro estructurado de cada ejecución del agente en
  `bitacora/ejecuciones.jsonl` (consulta, filtros, pasos, herramientas, duración,
  estado, error clasificado) con sección de métricas en la app y exportación CSV;
  esta bitácora de proyecto.
- Decidimos: registro **siempre**, incluidas las ejecuciones fallidas (alternativa
  descartada: registrar solo éxitos — invalidaría el análisis de errores que la rúbrica
  valora en C4.1).
- Evidencia: `src/bitacora.py` · `tests/test_bitacora.py` OK · sección "Bitácora" en la
  app.

### AAAA-MM-DD · [equipo]
- Hicimos: ...
- Decidimos: ... (alternativa descartada: ...)
- Evidencia: ...
- Dificultades: ...
- IA usada: ...

---

## 5. Métricas de validación de la ejecución

La sección **📓 Bitácora** de la app calcula estas métricas en vivo sobre el histórico;
transcribirlas aquí en cada corte de semana:

| Semana | Ejecuciones | Tasa de éxito | Duración promedio (s) | Errores por tipo |
|--------|-------------|---------------|----------------------|------------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

Interpretación esperada: la tasa de éxito debería estabilizarse alta (>80 %) con los
errores concentrados en los casos difíciles documentados (CP-03/CP-04), y la duración
promedio mantenerse en el orden de segundos. Una tasa que cae o latencias crecientes son
señales de datos desactualizados o degradación del proveedor LLM.
