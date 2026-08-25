"""Prueba del bucle del agente con un LLM simulado (sin red ni API key).

Ejecutar desde la raiz del proyecto:
    python3 tests/test_bucle_stub.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agent import AgenteMaquillaje  # noqa: E402
from src.config import Config  # noqa: E402
from src.tools import ToolError  # noqa: E402


class FuncionFake:
    def __init__(self, nombre, argumentos):
        self.name = nombre
        self.arguments = argumentos


class LlamadaFake:
    def __init__(self, id_, nombre, argumentos):
        self.id = id_
        self.function = FuncionFake(nombre, argumentos)

    def model_dump(self):
        return {"id": self.id, "type": "function",
                "function": {"name": self.function.name, "arguments": self.function.arguments}}


class MensajeFake:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class RespuestaFake:
    def __init__(self, mensaje):
        self.choices = [type("Eleccion", (), {"message": mensaje})()]


JSON_FINAL = """
{
  "interpretacion_consulta": "Busca labial SuperStay Matte Ink comparando detal vs mayorista.",
  "grupos_equivalentes": [
    {"nombre_canonico": "Labial liquido Maybelline SuperStay Matte Ink 5 ml",
     "marca": "Maybelline",
     "items": [
       {"fuente": "tienda_online", "id": "ret-002"},
       {"fuente": "distribuidor", "id": "dis-001"},
       {"fuente": "distribuidor", "id": "dis-003"}
     ]}
  ],
  "comparativo": [
    {"grupo": "Labial liquido Maybelline SuperStay Matte Ink 5 ml",
     "referencia_fuente_id": "ret-002", "proveedor": "MercadoLibre", "modalidad": "detal",
     "precio_unitario_cop": 54000, "cantidad_minima": 1, "unidades_a_comprar": 12,
     "costo_envio_cop": 8500, "costo_total_cop": 656500, "costo_unitario_efectivo_cop": 54708,
     "calificacion": 4.3, "ciudad_despacho": "Medellin", "ventajas": ["Compra flexible"],
     "limitaciones": ["Sin descuento por volumen"]},
    {"grupo": "Labial liquido Maybelline SuperStay Matte Ink 5 ml",
     "referencia_fuente_id": "dis-001", "proveedor": "Distribuidora Belleza Express",
     "modalidad": "mayorista", "precio_unitario_cop": 38000, "cantidad_minima": 12,
     "unidades_a_comprar": 12, "costo_envio_cop": 12000, "costo_total_cop": 468000,
     "costo_unitario_efectivo_cop": 39000, "calificacion": 4.6, "ciudad_despacho": "Bogota",
     "ventajas": ["Ahorro de 28.7% por unidad"], "limitaciones": ["Minimo 12 unidades"]}
  ],
  "recomendacion": {
    "opcion_ganadora_id": "dis-001",
    "criterio_aplicado": "menor costo total",
    "justificacion": "Comprar la caja mayorista cuesta 468000 COP (39000/unidad) frente a 656500 COP (54708/unidad) al detal en MercadoLibre: ahorro de 188500 COP.",
    "alternativa_sugerida": "Si no se quiere inmovilizar capital en 12 unidades, comprar al detal en ret-002.",
    "alertas": ["El despacho sale desde Bogota; verificar cobertura de envio."]
  },
  "datos_insuficientes": ["ret-002 no especifica tono en la publicacion"]
}
"""


class ClienteStub:
    """Simula ClienteLLM con una secuencia predefinida de respuestas."""

    def __init__(self):
        self.pasos = 0

    def chat(self, mensajes, tools=None):
        self.pasos += 1
        if self.pasos == 1:
            return RespuestaFake(MensajeFake(tool_calls=[
                LlamadaFake("c1", "buscar_en_tiendas", '{"consulta": "superstay matte ink"}'),
                LlamadaFake("c2", "consultar_distribuidores", '{"tipo": "labial", "marca": "Maybelline"}'),
            ]))
        if self.pasos == 2:
            return RespuestaFake(MensajeFake(tool_calls=[
                LlamadaFake("c3", "calcular_costo",
                            '{"precio_unitario_cop": 38000, "cantidad_unidades": 12, "costo_envio_cop": 12000}'),
                # llamada con herramienta inexistente para probar manejo de error
                LlamadaFake("c4", "herramienta_inventada", "{}"),
            ]))
        return RespuestaFake(MensajeFake(content=JSON_FINAL))


class ClienteStubConSalidaMala:
    """Primero responde texto no-JSON para probar la autocorreccion del bucle."""

    def __init__(self):
        self.pasos = 0

    def chat(self, mensajes, tools=None):
        self.pasos += 1
        if self.pasos == 1:
            return RespuestaFake(MensajeFake(content="Claro! Aqui tienes el analisis: ..."))
        return RespuestaFake(MensajeFake(content=JSON_FINAL))


class ClienteStubGanadoraFantasma:
    """Entrega JSON valido pero recomendando una opcion que NO esta en el comparativo."""

    def __init__(self):
        self.pasos = 0

    def chat(self, mensajes, tools=None):
        self.pasos += 1
        if self.pasos == 1:
            malo = JSON_FINAL.replace('"opcion_ganadora_id": "dis-001"', '"opcion_ganadora_id": "dis-999"')
            return RespuestaFake(MensajeFake(content=malo))
        return RespuestaFake(MensajeFake(content=JSON_FINAL))


def probar_recuperacion_json():
    agente = AgenteMaquillaje.__new__(AgenteMaquillaje)
    agente.llm = ClienteStubConSalidaMala()
    resultado = agente.ejecutar("prueba", {})
    assert resultado.ok, f"Debio recuperarse del JSON invalido: {resultado.error}"
    tipos = [p.tipo for p in resultado.pasos]
    assert "validacion_error" in tipos and "final" in tipos
    print("TEST RECUPERACION JSON INVALIDO: OK")


def probar_ganadora_fantasma():
    agente = AgenteMaquillaje.__new__(AgenteMaquillaje)
    agente.llm = ClienteStubGanadoraFantasma()
    resultado = agente.ejecutar("prueba", {})
    assert resultado.ok, "El validador cruzado debio corregir la ganadora fantasma en el reintento"
    assert any("validacion_error" in p.tipo for p in resultado.pasos)
    assert resultado.salida.recomendacion.opcion_ganadora_id == "dis-001"
    print("TEST VALIDACION CRUZADA GANADORA: OK")


def probar_csv_malformado():
    import csv as _csv
    import tempfile

    import src.tools as T

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    w = _csv.writer(tmp)
    w.writerow(["id", "nombre", "marca", "tipo", "presentacion", "tono", "distribuidor",
                "ciudad_despacho", "precio_unitario_detal_cop", "precio_unitario_mayorista_cop",
                "cantidad_minima_mayorista", "calificacion", "num_resenas", "stock_unidades",
                "costo_envio_cop", "beneficios"])
    w.writerow(["dis-999", "Producto nuevo", "", "labial", "5 ml", "", "Dist", "Bogota",
                "40000", "32000", "10", "4.5", "", "50", "9000", "ok"])  # num_resenas vacio
    tmp.close()
    original = T.ARCHIVO_DISTRIBUIDORES
    T.ARCHIVO_DISTRIBUIDORES = tmp.name
    try:
        T.consultar_distribuidores(tipo="labial")
        raise AssertionError("Debio fallar de forma controlada con ToolError")
    except ToolError as e:
        assert "dis-999" in str(e) and "num_resenas" in str(e), f"Mensaje poco util: {e}"
    finally:
        T.ARCHIVO_DISTRIBUIDORES = original
        Path(tmp.name).unlink()
    print("TEST CSV MALFORMADO (ToolError controlado): OK")


def main():
    agente = AgenteMaquillaje.__new__(AgenteMaquillaje)
    agente.llm = ClienteStub()
    resultado = agente.ejecutar("Necesito 12 labiales SuperStay para reventa", {"presupuesto_maximo_cop": 500000})

    assert resultado.ok, f"Fallo el bucle: {resultado.error}"
    tipos = [p.tipo for p in resultado.pasos]
    assert tipos.count("tool_llamada") == 3, f"Esperaba 3 tool calls exitosas, hubo {tipos}"
    assert any(p.tipo == "tool_error" for p in resultado.pasos), "No se registro el error de herramienta inventada"
    s = resultado.salida
    assert s.recomendacion.opcion_ganadora_id == "dis-001"
    assert len(s.comparativo) == 2 and len(s.grupos_equivalentes) == 1
    assert s.comparativo[0].costo_total_cop == 656500

    print("PASO LOG:")
    for p in resultado.pasos:
        print(f"  [{p.tipo}] paso {p.paso}: {p.detalle[:90]}")
    print("\nTEST BUCLE STUB: OK")

    probar_recuperacion_json()
    probar_ganadora_fantasma()
    probar_csv_malformado()
    print("\nTODOS LOS TESTS: OK")


if __name__ == "__main__":
    main()
