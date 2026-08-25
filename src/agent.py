"""Bucle de decision del agente: interpreta, consulta herramientas y entrega JSON validado."""
import json
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from .config import Config
from .llm import ClienteLLM, ErrorLLM
from .models import SalidaAgente
from .tools import REGISTRO_HERRAMIENTAS, ToolError

RUTA_PROMPT_SISTEMA = Path(__file__).resolve().parent.parent / "prompts" / "sistema_v1.txt"
MAX_PASOS = 10
MAX_INTENTOS_JSON_FINAL = 2

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "buscar_en_tiendas",
            "description": "Busca productos de maquillaje en el listado capturado de tiendas online colombianas (retail).",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {"type": "string", "description": "Texto libre: producto a buscar."},
                    "marca": {"type": "string", "description": "Marca buscada (opcional)."},
                    "tipo": {"type": "string", "description": "Categoria: labial, base, rimel, paleta_sombras, corrector, rubor, fijador, delineador, polvo_compacto, primer, brillo_labial, accesorios (opcional)."},
                },
                "required": ["consulta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_distribuidores",
            "description": "Consulta catalogos de distribuidores mayoristas con precio detal y mayorista, cantidad minima y despacho.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "description": "Categoria del producto (opcional)."},
                    "marca": {"type": "string", "description": "Marca buscada (opcional)."},
                    "consulta": {"type": "string", "description": "Texto libre adicional (opcional)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_costo",
            "description": "Calcula costo total (subtotal + envio) y costo unitario efectivo de una opcion de compra.",
            "parameters": {
                "type": "object",
                "properties": {
                    "precio_unitario_cop": {"type": "number", "description": "Precio por unidad en COP."},
                    "cantidad_unidades": {"type": "integer", "description": "Unidades a comprar."},
                    "costo_envio_cop": {"type": "number", "description": "Costo de envio en COP (0 si es gratis)."},
                },
                "required": ["precio_unitario_cop", "cantidad_unidades"],
            },
        },
    },
]


@dataclass
class PasoLog:
    paso: int
    tipo: str  # "tool_llamada" | "tool_error" | "validacion_error" | "final" | "error"
    detalle: str


@dataclass
class ResultadoAgente:
    salida: SalidaAgente | None = None
    pasos: list[PasoLog] = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.salida is not None


def _extraer_json(texto: str) -> dict:
    """Extrae un objeto JSON de la respuesta, tolerando cercas de codigo."""
    limpio = texto.strip()
    if limpio.startswith("```"):
        limpio = limpio.split("\n", 1)[1] if "\n" in limpio else limpio
        if limpio.rstrip().endswith("```"):
            limpio = limpio.rstrip()[:-3]
    return json.loads(limpio.strip())


class AgenteMaquillaje:
    def __init__(self, config: Config):
        self.llm = ClienteLLM(config)

    def ejecutar(self, consulta_usuario: str, filtros: dict) -> ResultadoAgente:
        resultado = ResultadoAgente()
        try:
            prompt_sistema = RUTA_PROMPT_SISTEMA.read_text(encoding="utf-8")
        except FileNotFoundError:
            resultado.error = f"No se encontro el prompt versionado en {RUTA_PROMPT_SISTEMA}"
            return resultado

        filtros_txt = json.dumps(filtros, ensure_ascii=False, indent=2)
        mensajes: list[dict] = [
            {"role": "system", "content": prompt_sistema},
            {
                "role": "user",
                "content": (
                    f"Solicitud del usuario: {consulta_usuario}\n\n"
                    f"Filtros configurados (respetalos):\n{filtros_txt}"
                ),
            },
        ]

        for n_paso in range(1, MAX_PASOS + 1):
            try:
                respuesta = self.llm.chat(mensajes, tools=TOOLS_SCHEMA)
            except ErrorLLM as e:
                resultado.pasos.append(PasoLog(n_paso, "error", str(e)))
                resultado.error = str(e)
                return resultado

            eleccion = respuesta.choices[0]
            llamadas = getattr(eleccion.message, "tool_calls", None)

            if not llamadas:
                contenido = eleccion.message.content or ""
                try:
                    datos = _extraer_json(contenido)
                    resultado.salida = SalidaAgente.model_validate(datos)
                    resultado.pasos.append(PasoLog(n_paso, "final", "JSON final validado correctamente."))
                    return resultado
                except json.JSONDecodeError as e:
                    resultado.pasos.append(
                        PasoLog(n_paso, "validacion_error", f"Salida sin JSON parseable ({e}); se pide correccion.")
                    )
                    mensajes.append({"role": "assistant", "content": contenido})
                    mensajes.append(
                        {
                            "role": "user",
                            "content": "Tu respuesta no es JSON valido. Responde NUEVAMENTE solo con el "
                            "objeto JSON del contrato, sin texto adicional ni bloques de codigo.",
                        }
                    )
                except ValidationError as e:
                    if len([p for p in resultado.pasos if p.tipo == "validacion_error"]) >= MAX_INTENTOS_JSON_FINAL:
                        resultado.error = f"El modelo no cumplio el contrato JSON tras varios intentos: {e.errors()[0]}"
                        resultado.pasos.append(PasoLog(n_paso, "error", resultado.error))
                        return resultado
                    resultado.pasos.append(
                        PasoLog(
                            n_paso,
                            "validacion_error",
                            f"JSON invalido segun contrato: {e.errors()[0]['msg']} en campo {e.errors()[0]['loc']}",
                        )
                    )
                    mensajes.append({"role": "assistant", "content": contenido})
                    mensajes.append(
                        {
                            "role": "user",
                            "content": "El JSON incumple el contrato de salida. Corrige el campo indicado y "
                            f"reenvia SOLO el JSON completo. Detalle: {str(e)[:600]}",
                        }
                    )
                continue

            mensajes.append(
                {
                    "role": "assistant",
                    "content": eleccion.message.content or "",
                    "tool_calls": [tc.model_dump() for tc in llamadas],
                }
            )

            for llamada in llamadas:
                nombre = llamada.function.name
                argumentos_raw = llamada.function.arguments
                try:
                    args = json.loads(argumentos_raw or "{}")
                    funcion = REGISTRO_HERRAMIENTAS.get(nombre)
                    if funcion is None:
                        raise ToolError(f"Herramienta inexistente: {nombre}")
                    salida_tool = funcion(**args)
                    resultado.pasos.append(
                        PasoLog(
                            n_paso,
                            "tool_llamada",
                            f"{nombre}({json.dumps(args, ensure_ascii=False)}) -> "
                            + (f"{salida_tool.get('total_encontrados', '')} resultados"
                               if isinstance(salida_tool, dict) and "total_encontrados" in salida_tool
                               else str(salida_tool)),
                        )
                    )
                    mensajes.append(
                        {
                            "role": "tool",
                            "tool_call_id": llamada.id,
                            "content": json.dumps(salida_tool, ensure_ascii=False),
                        }
                    )
                except (json.JSONDecodeError, TypeError, ValueError, ToolError) as e:
                    detalle = (
                        f"Argumentos no parseables para {nombre}: {argumentos_raw[:200]}"
                        if isinstance(e, json.JSONDecodeError)
                        else f"{nombre} fallo: {e}"
                    )
                    resultado.pasos.append(PasoLog(n_paso, "tool_error", detalle))
                    mensajes.append(
                        {
                            "role": "tool",
                            "tool_call_id": llamada.id,
                            "content": json.dumps({"error": detalle}, ensure_ascii=False),
                        }
                    )

        resultado.error = (
            "El agente alcanzo el numero maximo de pasos sin entregar una respuesta valida "
            f"({MAX_PASOS}). Consulta demasiado compleja o modelo poco capaz."
        )
        resultado.pasos.append(PasoLog(MAX_PASOS, "error", resultado.error))
        return resultado
