# Instrucciones para usar Agente Belleza CO (para la contraparte)

## Que hace este programa

Es un asistente que compara precios de maquillaje entre tiendas online y tus
distribuidores mayoristas. Tu le dices que necesitas comprar y te devuelve:
la lista de opciones encontradas, cuanto costaria el pedido completo (con envio),
y su recomendacion de donde comprar. Ademas puedes descargar la comparacion en Excel/CSV.

## Como ponerlo a andar (una sola vez)

1. Pide al equipo que te instale el programa (o sigue el paso 2).
2. En tu computador necesitas Python gratis (python.org). Luego:
   - Descarga la carpeta `agente-maquillaje`.
   - Abre la aplicacion "Terminal" y escribe:
     ```
     cd ruta/a/agente-maquillaje
     pip install -r requirements.txt
     streamlit run app.py
     ```
3. Se abre una pagina en tu navegador. Ya puedes usarlo siempre que quieras repitiendo
   el ultimo comando.

## Como usarlo (cada vez)

1. En la barra izquierda escoge: tipo de producto, cuantas unidades necesitas,
   tu presupuesto maximo y si prefieres comprar al detal o al por mayor.
2. Arriba escribe que necesitas, por ejemplo:
   *"Necesito 12 labiales Maybelline SuperStay tono 80 para reventa"*.
3. Pulsa **Ejecutar agente** y espera unos segundos.
4. Lee la tarjeta verde (la recomendacion) y revisa la tabla comparativa.
5. Si quieres guardarla, pulsa **Descargar comparativo (CSV)** y abrelo en Excel.

## Como darte cuenta de que se equivoco

- Si ves una advertencia amarilla de "Datos insuficientes", el agente encontro productos
  dudosos (sin marca confirmada): no confies en esa opcion sin verificar.
- Compara el "Costo total estimado" con lo que ya conoces: si algo supera tu presupuesto,
  el filtro estaba mal puesto o no existe opcion dentro de el (el aviso te lo dira).
- Seccion "Decisiones del agente": muestra que consulto exactamente. Si busco otra cosa,
  reformula tu pregunta con marca y producto claros.
- Importante: los precios vienen de una lista guardada (vease fecha de captura). Antes de
  comprar, confirma el precio final con el proveedor: el agente recomienda, nunca compra.

## Si algo falla

| Mensaje | Que significa | Que hacer |
|---|---|---|
| "Falta OPENAI_API_KEY" | Falta configurar la clave | Pedir ayuda al equipo o seguir README.md |
| "limite de uso (rate limit)" | El servicio de IA esta saturado | Esperar 1 minuto y volver a intentar |
| "alcanzo el numero maximo de pasos" | La consulta fue muy compleja | Simplificar: un tipo de producto por consulta |
| Pagina no abre | El programa no esta corriendo | Repetir `streamlit run app.py` en la Terminal |
