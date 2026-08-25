"""Agente Belleza CO - interfaz Streamlit.

Ejecutar desde la raiz del proyecto:
    streamlit run app.py
"""
import json

import pandas as pd
import streamlit as st

from src.agent import AgenteMaquillaje
from src.config import cargar_config
from src.llm import ErrorLLM
from src.tools import buscar_en_tiendas, consultar_distribuidores

st.set_page_config(page_title="Agente Belleza CO", page_icon="💄", layout="wide")

TIPOS_PRODUCTO = [
    "", "labial", "base", "rimel", "paleta_sombras", "corrector", "rubor",
    "fijador", "delineador", "polvo_compacto", "primer", "brillo_labial", "accesorios",
]
CRITERIOS = {
    "Menor costo total": "menor costo total",
    "Mejor calidad-precio": "mejor relacion calidad-precio",
    "Menor inversion inicial": "menor inversion inicial (priorizar cantidad minima baja)",
    "Mejor calificacion del proveedor": "mejor calificacion del proveedor",
}

# ---------------------------------------------------------------------------
# Datos auxiliares para filtros
# ---------------------------------------------------------------------------
@st.cache_data
def cargar_catalogos():
    tiendas = buscar_en_tiendas("")["productos"]
    distribuidores = consultar_distribuidores()["productos"]
    marcas = sorted({p["marca"] for p in tiendas} | {p["marca"] for p in distribuidores})
    ciudades = sorted({p["ciudad_despacho"] for p in tiendas} | {p["ciudad_despacho"] for p in distribuidores})
    return tiendas, distribuidores, marcas, ciudades


def cop(valor) -> str:
    try:
        return f"${float(valor):,.0f}".replace(",", ".")
    except (TypeError, ValueError):
        return "-"


config = cargar_config()
tiendas, distribuidores, marcas, ciudades = cargar_catalogos()

# ---------------------------------------------------------------------------
# Barra lateral: filtros y criterios
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Filtros de compra")
    tipo_producto = st.selectbox("Tipo de producto", TIPOS_PRODUCTO,
                                 format_func=lambda t: t or "(todos)")
    unidades_objetivo = st.number_input("Unidades que necesitas", min_value=1, value=12)
    presupuesto = st.number_input("Presupuesto maximo total (COP)", min_value=0, value=500000,
                                  step=50000, help="0 = sin limite")
    modalidad = st.radio("Modalidad preferida", ["Indiferente", "Detal", "Mayorista"])
    marcas_pref = st.multiselect("Marcas de interes (opcional)", marcas)
    ciudad = st.selectbox("Ciudad de entrega preferida", ["(cualquiera)"] + ciudades)
    criterio = st.selectbox("Criterio de decision", list(CRITERIOS))

    st.divider()
    st.caption(
        "**Motor LLM:** "
        f"`{config.modelo}`\n\nClave API cargada desde `.env`: "
        + ("si" if config.api_key else "**NO** (crea tu .env)")
    )

# ---------------------------------------------------------------------------
# Panel principal
# ---------------------------------------------------------------------------
st.title("💄 Agente Belleza CO")
st.markdown(
    "Comparador automatico de productos de maquillaje entre **tiendas online** (retail) y "
    "**distribuidores mayoristas**, para decisiones de compra informadas."
)

consulta = st.text_area(
    "Que necesitas comprar?",
    placeholder="Ej: Necesito labiales liquidos Maybelline SuperStay para reventa, 12 unidades",
    height=90,
)
ejecutar = st.button("🚀 Ejecutar agente", type="primary", disabled=not consulta.strip())

if ejecutar:
    if not config.api_key:
        st.error(
            "No hay OPENAI_API_KEY configurada. Copia `.env.example` como `.env`, coloca tu clave "
            "y recarga la pagina. Nunca escribas la clave en el codigo."
        )
        st.stop()

    filtros = {
        "tipo_producto": tipo_producto or None,
        "unidades_objetivo": int(unidades_objetivo),
        "presupuesto_maximo_cop": int(presupuesto) if presupuesto > 0 else None,
        "modalidad_preferida": modalidad.lower(),
        "marcas_preferidas": marcas_pref,
        "ciudad_entrega_preferida": None if ciudad.startswith("(") else ciudad,
        "criterio_recomendacion": CRITERIOS[criterio],
    }

    with st.spinner("El agente esta consultando fuentes, agrupando equivalentes y calculando costos..."):
        agente = AgenteMaquillaje(config)
        resultado = agente.ejecutar(consulta, filtros)

    with st.expander("🔍 Decisiones del agente (trazabilidad)", expanded=False):
        for paso in resultado.pasos:
            icono = {"tool_llamada": "🔧", "tool_error": "⚠️", "validacion_error": "🔁", "final": "✅", "error": "❌"}[paso.tipo]
            st.markdown(f"`paso {paso.paso}` {icono} {paso.detalle}")

    if not resultado.ok:
        st.error(f"**El agente no pudo completar la tarea:** {resultado.error}")
        st.stop()

    salida = resultado.salida

    st.subheader(f"📌 {salida.interpretacion_consulta}")

    # --- Recomendacion ---
    ganadora = next((o for o in salida.comparativo if o.referencia_fuente_id == salida.recomendacion.opcion_ganadora_id), None)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Opcion recomendada", ganadora.proveedor if ganadora else "-",
                  f"{ganadora.modalidad.capitalize()}" if ganadora else None)
    with col2:
        st.metric("Costo total estimado", cop(ganadora.costo_total_cop) if ganadora else "-",
                  f"{ganadora.unidades_a_comprar} u." if ganadora else None)
    with col3:
        st.metric("Costo unitario efectivo", cop(ganadora.costo_unitario_efectivo_cop) if ganadora else "-")

    st.success(
        f"**Recomendacion ({salida.recomendacion.criterio_aplicado}):** {salida.recomendacion.justificacion}"
    )
    if salida.recomendacion.alternativa_sugerida:
        st.info(f"**Alternativa:** {salida.recomendacion.alternativa_sugerida}")
    for alerta in salida.recomendacion.alertas:
        st.warning(f"⚠️ {alerta}")

    # --- Tabla comparativa ---
    st.subheader("📊 Comparativo de opciones")
    if salida.comparativo:
        df = pd.DataFrame(salida.comparativo)
        df["calificacion"] = pd.to_numeric(df["calificacion"], errors="coerce").round(1)
        columnas = {
            "grupo": "Producto (grupo)",
            "proveedor": "Proveedor",
            "modalidad": "Modalidad",
            "precio_unitario_cop": "Precio unit.",
            "cantidad_minima": "Cant. minima",
            "unidades_a_comprar": "Unidades",
            "costo_envio_cop": "Envio",
            "costo_total_cop": "Costo total",
            "costo_unitario_efectivo_cop": "Costo unit. efectivo",
            "calificacion": "Calif.",
            "ciudad_despacho": "Despacho desde",
            "ventajas": "Ventajas",
            "limitaciones": "Limitaciones",
        }
        ver = df[list(columnas)].rename(columns=columnas).copy()
        for c in ("Precio unit.", "Envio", "Costo total", "Costo unit. efectivo"):
            ver[c] = ver[c].map(cop)
        st.dataframe(ver, use_container_width=True)
        st.download_button(
            "⬇️ Descargar comparativo (CSV)",
            data=ver.to_csv(index=False).encode("utf-8"),
            file_name="comparativo_maquillaje.csv",
            mime="text/csv",
        )
    else:
        st.info("No hay opciones suficientes para comparar.")

    # --- Grupos equivalentes ---
    with st.expander("🧩 Productos equivalentes identificados"):
        for grupo in salida.grupos_equivalentes:
            ids = ", ".join(f"{i.id} ({i.fuente.replace('_', ' ')})" for i in grupo.items)
            st.markdown(f"- **{grupo.nombre_canonico}** · {grupo.marca}: {ids}")

    if salida.datos_insuficientes:
        st.warning("**Datos insuficientes / alertas de calidad:**\n\n" +
                   "\n".join(f"- {d}" for d in salida.datos_insuficientes))

    with st.expander("Ver JSON crudo de la respuesta"):
        st.code(json.dumps(salida.model_dump(), ensure_ascii=False, indent=2), language="json")
