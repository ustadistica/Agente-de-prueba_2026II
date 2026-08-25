# 💄 Agente Belleza CO

Agente de IA que compara productos de maquillaje entre **tiendas online colombianas** (retail)
y **distribuidores mayoristas**, y recomienda la opcion de compra mas conveniente para
emprendimientos de belleza segun criterios configurables (presupuesto, unidades, modalidad,
ciudad de entrega).

No es un script fijo: es un **ciclo de decision** donde un LLM interpreta la solicitud,
elige que consultar, agrupa productos equivalentes aunque cambien nombre o vendedor,
delega la aritmetica en una herramienta determinista y entrega una recomendacion justificada
con cifras.

## Arquitectura

```
 Usuario (consulta + filtros)
        │
        ▼
 ┌───────────────────────────────────────────────┐
 │ Bucle del agente (max 10 pasos)               │
 │  1. Interpreta la solicitud                   │
 │  2. Decide que herramientas invocar           │
 │     ├─ buscar_en_tiendas()      → tiendas_online.json        │
 │     ├─ consultar_distribuidores() → catalogo_distribuidores.csv │
 │     └─ calcular_costo()         → aritmetica determinista   │
 │  3. Agrupa equivalentes + calcula opciones    │
 │  4. Emite JSON validado con pydantic          │
 └───────────────────────────────────────────────┘
        │  errores gestionados por tipo:
        │  timeout → reintento · rate limit → backoff · tool invalida → feedback
        │  JSON invalido → correccion guiada · max pasos → parada controlada
        ▼
 Streamlit: log de decisiones · metricas · tabla comparativa · recomendacion
```

## Instalacion desde cero (otra maquina)

Requisitos: Python 3.10+ y acceso a internet.

```bash
cd agente-maquillaje
python3 -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # abre .env y coloca TU clave de API
streamlit run app.py
```

Se abre `http://localhost:8501`. Coloca tu consulta, ajusta filtros en la barra lateral y
pulsa **Ejecutar agente**.

## Despliegue en Streamlit Community Cloud (gratis)

La app puede quedar publicada en internet para que la contraparte la use sin instalar nada:

1. Entra a **https://share.streamlit.io** y inicia sesion con **Sign in with GitHub**
   (usa una cuenta con acceso al repo `ustadistica/Agente-de-prueba_2026II`).
2. Si el repo es de una organizacion, autoriza el acceso:
   GitHub → Settings → Applications → Authorized OAuth Apps → **Streamlit** → Grant.
3. Pulsa **Create app → Deploy a public app from GitHub**.
4. Selecciona: Repository `ustadistica/Agente-de-prueba_2026II` · Branch `main` ·
   Main file `app.py`. (En Advanced settings puedes fijar Python 3.12.)
5. Antes del primer uso, abre el menu de la app (⋯) → **Settings → Secrets** y pega:

   ```toml
   OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
   OPENAI_API_KEY = "TU_CLAVE_DE_GEMINI"
   LLM_MODEL = "gemini-2.0-flash"
   LLM_TEMPERATURE = "0.2"
   ```

6. Reboot the app. Listo: la URL publica queda para compartir.

Las credenciales NUNCA van en el repositorio: localmente viven en `.env` y en la nube en
los Secrets del dashboard (el codigo lee ambos: `src/config.py -> _valor`).

### Configurar la clave API (sin tocar el codigo)

El cliente usa cualquier endpoint compatible con la API de OpenAI; solo editas `.env`:

| Opcion | OPENAI_BASE_URL | LLM_MODEL | Notas |
|---|---|---|---|
| Google Gemini (gratis) | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.0-flash` | Clave en aistudio.google.com |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` | De pago |
| Ollama local | `http://localhost:11434/v1` | `llama3.1:8b` | Gratis, privado, requiere RAM |

**Criterios de eleccion usados en este proyecto:** costo (Gemini free tier gana para demo),
privacidad de datos del negocio (Ollama local nunca envia datos afuera), calidad de
razonamiento (gpt-4o-mini mejor en matching difuso), latencia (flash < gpt).
Se eligio Gemini como default del prototipo por costo cero y buena relacion calidad/latencia;
el codigo no cambia entre proveedores.

## Estructura

```
agente-maquillaje/
├── app.py                      # interfaz Streamlit
├── src/
│   ├── config.py               # configuracion via variables de entorno (.env)
│   ├── models.py               # modelos pydantic + contrato de salida del agente
│   ├── tools.py                # 3 herramientas invocables (datos + aritmetica)
│   ├── llm.py                  # cliente LLM con reintentos por tipo de error
│   └── agent.py                # bucle de decision del agente
├── data/
│   ├── tiendas_online.json     # listado capturado de tiendas retail (actualizable)
│   └── catalogo_distribuidores.csv  # precios detal/mayorista de distribuidores
├── prompts/
│   ├── sistema_v1.txt          # prompt del sistema (versionado, lo carga agent.py)
│   └── prompts_v1.md           # documentacion de versiones e iteraciones
├── tests/
│   └── test_bucle_stub.py      # prueba del bucle con LLM simulado (sin red ni clave)
└── docs/
    ├── casos_prueba.md
    ├── memoria_tecnica_plantilla.md
    ├── constancia_encargo_plantilla.md
    └── instrucciones_contraparte.md
```

## Actualizar los datos

Los archivos de `data/` son la fuente de verdad del agente (captura del 20-08-2026):
- `tiendas_online.json`: agrega/edita registros de tiendas con el mismo esquema.
- `catalogo_distribuidores.csv`: lista de precios del distribuidor (detal, mayorista,
  cantidad minima, despacho, envio).
Ninguna credencial de terceros es necesaria: son datos ya existentes y accesibles.

## Pruebas

```bash
python3 tests/test_bucle_stub.py   # bucle completo con LLM simulado (no gasta tokens)
```

Casos manuales (incluido uno donde el agente DEBE fallar): ver `docs/casos_prueba.md`.

## Limitaciones conocidas

- Los datos reflejan una captura puntual; precios y stock cambian (mitigacion: actualizar
  `data/` periodicamente; el meta del JSON registra la fecha de captura).
- No hay transacciones ni pagos: solo recomendacion informada.
- Si el proveedor LLM esta caido o sin cuota, el agente informa el error en lugar de inventar.
