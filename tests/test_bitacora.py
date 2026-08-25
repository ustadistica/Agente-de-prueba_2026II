"""Pruebas de la bitacora de ejecucion (sin red ni API key).

Ejecutar desde la raiz del proyecto:
    python3 tests/test_bitacora.py
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import bitacora  # noqa: E402
from src.agent import PasoLog  # noqa: E402


class ResultadoFake:
    def __init__(self, ok, pasos, error=None):
        self.ok = ok
        self.pasos = pasos
        self.error = error
        self.salida = None


def main():
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    original = bitacora.ARCHIVO_BITACORA
    bitacora.ARCHIVO_BITACORA = Path(tmp.name)

    pasos_ok = [
        PasoLog(1, "tool_llamada", 'buscar_en_tiendas({"consulta": "labial"}) -> 4 resultados'),
        PasoLog(1, "tool_llamada", 'consultar_distribuidores({"tipo": "labial"}) -> 3 resultados'),
        PasoLog(2, "tool_error", "herramienta_inventada fallo: Herramienta inexistente"),
        PasoLog(3, "final", "JSON final validado correctamente."),
    ]
    r1 = bitacora.registrar_ejecucion(
        consulta="Necesito 12 labiales SuperStay",
        filtros={"unidades_objetivo": 12},
        resultado=ResultadoFake(ok=True, pasos=pasos_ok),
        modelo="gemini-2.0-flash",
        duracion_seg=8.34,
    )
    r2 = bitacora.registrar_ejecucion(
        consulta="paletas naked",
        filtros={},
        resultado=ResultadoFake(ok=False, pasos=[], error="El modelo no respondio tras 3 reintentos (timeout)."),
        modelo="gemini-2.0-flash",
        duracion_seg=61.2,
    )

    assert r1["estado"] == "ok" and r2["estado"] == "error"
    assert r1["herramientas_invocadas"] == ["buscar_en_tiendas", "consultar_distribuidores"]
    assert r2["tipo_error"] == "timeout"
    assert r1["recomendacion_id"] is None  # salida falsa sin recomendacion

    # Linea corrupta manual: la lectura debe tolerarla
    with open(tmp.name, "a", encoding="utf-8") as f:
        f.write("esto no es json\n")

    registros = bitacora.leer_ejecuciones()
    assert len(registros) == 2, f"Esperaba 2 registros validos, hay {len(registros)}"
    assert registros[0]["id"] == r2["id"]  # mas reciente primero

    stats = bitacora.resumen(registros)
    assert stats["total"] == 2 and stats["exitosas"] == 1 and stats["errores"] == 1
    assert stats["errores_por_tipo"] == {"timeout": 1}
    assert stats["herramientas_mas_usadas"]["buscar_en_tiendas"] == 1
    assert 30 < stats["duracion_promedio_seg"] < 40

    # Validar JSON serializable completo (una linea = un registro consistente)
    json.dumps(registros[0], ensure_ascii=False)

    bitacora.ARCHIVO_BITACORA = original
    Path(tmp.name).unlink()
    print("TEST BITACORA: OK (registro, lectura tolerante, resumen y clasificacion de errores)")


if __name__ == "__main__":
    main()
