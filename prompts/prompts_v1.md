# Versionado de prompts — Agente Belleza CO

El prompt activo del sistema vive en `prompts/sistema_v1.txt` y el codigo lo carga desde ahi
(`src/agent.py -> RUTA_PROMPT_SISTEMA`). Al modificar el prompt se crea un archivo nuevo
(`sistema_v2.txt`) y se actualiza la ruta; NUNCA se sobreescribe la version anterior.
Asi queda evidencia de la iteracion exigida en la sustentacion.

---

## v1 (`prompts/sistema_v1.txt`) — version inicial

**Rol:** agente consultor de compras de maquillaje para emprendimientos colombianos.

**Contrato de salida:** JSON unico validado contra `SalidaAgente` (pydantic) con campos:
`interpretacion_consulta`, `grupos_equivalentes`, `comparativo`, `recomendacion`,
`datos_insuficientes`. El campo `opcion_ganadora_id` debe apuntar a una fila real del comparativo.

**Restricciones:**
- Todo dato proviene de herramientas (prohibido inventar productos o precios).
- La aritmetica de costos SOLO via `calcular_costo`.
- El precio mayorista exige alcanzar la cantidad minima.
- Tonos distintos no se agrupan si el usuario exige tono; publicaciones sin marca confirmada
  van a `datos_insuficientes` (no se agrupan con marcas reales).
- Justificaciones con cifras concretas.

**Justificacion de decisiones de diseno del prompt:**
| Decision | Alternativa descartada | Por que |
|---|---|---|
| JSON puro como contrato | Markdown libre | La tabla comparativa se renderiza automatica en Streamlit y se exporta CSV; JSON parseable evita alucinaciones de formato. |
| Aritmetica delegada a herramienta | Pedir al modelo que calcule | Los LLM fallan multiplicaciones largas; `calcular_costo` hace el calculo determinista y auditable. |
| Regla de re-busqueda antes de declarar vacio | Una sola busqueda literal | Las publicaciones varian ("SuperStay", "superstay matte ink", solo marca); sin re-formulacion el agente reportaba falsos vacios. |
| `datos_insuficientes` como salida explicita | Suponer datos faltantes | Obliga al agente a declarar incertidumbre (ej. publicacion generica "Paleta Naked" sin marca), clave para decisiones de compra reales. |

**Iteraciones registradas:** ninguna todavia (v1 es la version base del prototipo).
Criterio previsto para pasar a v2: si en pruebas el agente omite llamar `calcular_costo`
para alguna opcion, se endurecera la restriccion con ejemplo few-shot.

---

## Plantilla para futuras versiones

```
## vX (`prompts/sistema_vX.txt`) — fecha
Cambio realizado: ...
Motivo (evidencia de prueba): ...
Resultado esperado vs v anterior: ...
```
