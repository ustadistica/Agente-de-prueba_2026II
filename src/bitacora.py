"""Bitacora de ejecucion del agente: registro estructurado, persistente y auditable.

Cada ejecucion (exitosa o fallida) queda como una linea JSON en bitacora/ejecuciones.jsonl.
Ese archivo ES evidencia: se versiona en el repositorio para poder validar el uso real
del agente (cuando se ejecuto, que se consulto, cuanto tardo, que decidio, que fallo).

En despliegue en la nube el sistema de archivos puede ser efimero: alli la bitacora
de la sesion se conserva en memoria (st.session_state en la app) y el archivo se
escribe con mejor esfuerzo.
"""
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import BASE_DIR

ARCHIVO_BITACORA = BASE_DIR / "bitacora" / "ejecuciones.jsonl"

_PATRON_HERRAMIENTA = re.compile(r"^(\w+)\(")


def _clasificar_error(mensaje: str) -> str:
    """Agrupa el mensaje de error en una categoria estable para analisis."""
    m = (mensaje or "").lower()
    if "rate limit" in m:
        return "rate_limit"
    if "timeout" in m:
        return "timeout"
    if "api_key" in m or "credenciales" in m:
        return "credenciales"
    if "maximo de pasos" in m or "max pasos" in m:
        return "max_pasos"
    if "contrato json" in m:
        return "contrato_json"
    if "conexion" in m:
        return "conexion"
    if "prompt versionado" in m:
        return "configuracion"
    return "otro"


def _herramientas_de_pasos(pasos) -> list[str]:
    """Extrae los nombres de herramienta invocadas desde el log de pasos."""
    nombres = []
    for paso in pasos:
        if paso.tipo == "tool_llamada":
            coincidencia = _PATRON_HERRAMIENTA.match(paso.detalle)
            if coincidencia:
                nombres.append(coincidencia.group(1))
    return nombres


def registrar_ejecucion(
    consulta: str,
    filtros: dict,
    resultado,
    modelo: str,
    duracion_seg: float,
) -> dict[str, Any]:
    """Registra una ejecucion del agente y la agrega a la bitacora persistente.

    Args:
        consulta: texto consultado por el usuario.
        filtros: filtros aplicados (presupuesto, unidades, modalidad...).
        resultado: objeto ResultadoAgente (con .ok, .pasos, .error, .salida).
        modelo: nombre del modelo LLM utilizado.
        duracion_seg: duracion total de la ejecucion en segundos.

    Returns:
        El registro dict creado (aun si el archivo no pudo escribirse).
    """
    salida = getattr(resultado, "salida", None)
    tipos = Counter(p.tipo for p in resultado.pasos)
    registro = {
        "id": datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3],
        "fecha_hora": datetime.now().isoformat(timespec="seconds"),
        "consulta": consulta[:200],
        "filtros": filtros,
        "modelo": modelo,
        "duracion_seg": round(duracion_seg, 2),
        "estado": "ok" if resultado.ok else "error",
        "error": (resultado.error or None),
        "tipo_error": None if resultado.ok else _clasificar_error(resultado.error or ""),
        "num_pasos": len(resultado.pasos),
        "pasos_por_tipo": dict(tipos),
        "herramientas_invocadas": _herramientas_de_pasos(resultado.pasos),
        "num_grupos_equivalentes": len(salida.grupos_equivalentes) if salida else 0,
        "num_opciones_comparativo": len(salida.comparativo) if salida else 0,
        "recomendacion_id": salida.recomendacion.opcion_ganadora_id if salida else None,
        "pasos": [
            {"paso": p.paso, "tipo": p.tipo, "detalle": p.detalle[:120]} for p in resultado.pasos
        ],
    }
    try:
        ARCHIVO_BITACORA.parent.mkdir(parents=True, exist_ok=True)
        with open(ARCHIVO_BITACORA, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    except OSError:
        # Entorno de solo lectura (p. ej. despliegue en la nube): la ejecucion
        # sigue registrandose en memoria de sesion; no se interrumpe nada.
        pass
    return registro


def leer_ejecuciones(limite: int = 200) -> list[dict[str, Any]]:
    """Lee las ultimas ejecuciones registradas (mas recientes primero).

    Tolera lineas corruptas saltandolas: la bitacora nunca rompe la app.
    """
    if not ARCHIVO_BITACORA.exists():
        return []
    registros: list[dict[str, Any]] = []
    try:
        with open(ARCHIVO_BITACORA, encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    registros.append(json.loads(linea))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return list(reversed(registros))[:limite]


def resumen(ejecuciones: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcula metricas agregadas de validacion sobre un conjunto de ejecuciones."""
    total = len(ejecuciones)
    if total == 0:
        return {
            "total": 0, "exitosas": 0, "errores": 0, "tasa_exito": "-",
            "duracion_promedio_seg": 0.0, "errores_por_tipo": {}, "herramientas_mas_usadas": {},
        }
    exitosas = sum(1 for e in ejecuciones if e.get("estado") == "ok")
    duraciones = [float(e.get("duracion_seg") or 0) for e in ejecuciones]
    errores_por_tipo = Counter(
        e.get("tipo_error") or "otro" for e in ejecuciones if e.get("estado") != "ok"
    )
    herramientas = Counter()
    for e in ejecuciones:
        herramientas.update(e.get("herramientas_invocadas") or [])
    return {
        "total": total,
        "exitosas": exitosas,
        "errores": total - exitosas,
        "tasa_exito": f"{100 * exitosas / total:.0f}%",
        "duracion_promedio_seg": round(sum(duraciones) / total, 2),
        "errores_por_tipo": dict(errores_por_tipo),
        "herramientas_mas_usadas": dict(herramientas.most_common(3)),
    }
