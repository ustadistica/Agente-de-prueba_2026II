# Casos de prueba — Agente Belleza CO

Protocolo: ejecutar `streamlit run app.py`, configurar los filtros indicados y comparar la
salida contra el resultado esperado. Los casos CP-03 y CP-04 son **fallos documentados**:
el agente debe detectarlos y reportarlos honestamente (asi se demuestran los limites).

| ID | Escenario | Filtros | Resultado esperado | Estado |
|---|---|---|---|---|
| CP-01 | Exito: compra mayorista | Consulta: *"Necesito 12 labiales Maybelline SuperStay Matte Ink para reventa"* · criterio menor costo total · unidades 12 | Agrupa ret-001/002/003/026 y dis-001/002/003 como equivalentes; recomienda la caja mayorista (dis-001 o dis-002, ~$37.000–38.000/u) frente al detal (~$54.000+); justifica con ahorro calculado via `calcular_costo`. | ⚙️ mecanica verificada con LLM simulado · ⏳ pendiente con LLM real |
| CP-02 | Presupuesto fuerza detal | Igual a CP-01 pero presupuesto maximo $400.000 | La caja cuesta ~$468.000 > presupuesto; el agente debe descartar/relegar mayorista y recomendar la mejor opcion detal dentro del presupuesto (o alertar que ninguna cumple). | ⏳ pendiente |
| CP-03 | **FALLO ESPERADO**: publicacion generica sin marca | Consulta: *"quiero comprar paletas Naked baratas"* | La unica coincidencia es ret-022 ("Paleta Naked" sin marca, calificacion 3.9, marcada posible replica). El agente NO debe agruparla con Huda Beauty ni recomendarla como equivalente confiable; debe registrarla en `datos_insuficientes` con la alerta de calidad. Si aun asi la lista, debe advertir el riesgo de replica. | ⏳ pendiente |
| CP-04 | **FALLO ESPERADO**: producto inexistente en fuentes | Consulta: *"mascarilla de pestañas magnetica Vizzela 24 horas"* | Ninguna fuente contiene ese producto. El agente debe reformular busquedas (sinonimos/marca/tipo), agotar intentos y responder con comparativo vacio y explicacion clara, SIN inventar productos ni precios. | ⏳ pendiente |
| CP-05 | Stock insuficiente | Consulta: *"10 fijadores Urban Decay All Nighter"* · unidades 10 | El distribuidor dis-009 tiene minimo 6 pero stock maximo 8 < 10; el detallista ret-012 tiene solo 6 uds. El agente debe marcar limitaciones de stock en ambos y proponer combinacion parcial o alternativa. | ⏳ pendiente |
| CP-06 | Tono exigido | Igual a CP-01 pero consulta exige *"tono 80 Ruler exacto"* | ret-002 no especifica tono: debe quedar fuera del grupo equivalente o marcarse como incierta en `datos_insuficientes`; la recomendacion debe priorizar opciones con tono confirmado (dis-001, dis-002). | ⏳ pendiente |
| CP-07 | Criterio calidad-precio | Consulta libre sobre rimels · criterio mejor relacion calidad-precio | Compara Sky High (4.6–4.8) vs Colossal (4.4–4.5); la eleccion puede variar segun costo unitario efectivo, pero la justificacion debe citar ambas cifras. | ⏳ pendiente |

> Nota de honestidad sobre la columna Estado: "mecanica verificada con LLM simulado"
> significa que `tests/test_bucle_stub.py` demuestra que el bucle ejecuta herramientas,
> maneja errores y valida el JSON contra el contrato. NO demuestra que un modelo real
> tome las decisiones esperadas en cada caso: eso se verifica ejecutando cada CP con la
> clave API configurada y registrando la salida en la tabla del apartado siguiente.
> Los fallos CP-03 y CP-04 dependen del comportamiento real del modelo y deben evidenciarse
> antes de la sustentacion.

## Registro de ejecucion

Completar durante las pruebas semana 3 (evidencia para sustentacion):

```
Fecha | Caso | Ejecuto | Resultado observado | Desviacion | Accion
------|------|---------|--------------------|------------|-------
```

## Por que falla donde falla (analisis)

- **CP-03**: el matching semantico no puede verificar autenticidad. Un nombre generico
  "Naked" coincide lexicalmente con la linea "Naked" de Urban Decay, pero el catalogo no
  contiene evidencia de marca; agruparlo seria una alucinacion de equivalencia. El prompt v1
  lo bloquea explicitamente y deriva a `datos_insuficientes`.
- **CP-04**: el agente depende de datos existentes en `data/`. No navega internet en tiempo
  real (decision de alcance: evitar scraping fragil y permisos de terceros). Su limite es el
  inventario de la captura; la mitigacion es actualizar los archivos.
