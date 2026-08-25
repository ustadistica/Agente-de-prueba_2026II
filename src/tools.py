"""Herramientas (tools) que el agente puede invocar durante su ciclo de decision.

Cada herramienta es una funcion determinista y verificable. El agente NO inventa
datos: todo lo que reporta proviene de una de estas herramientas.
"""
import json
import re
from typing import Any

from .config import ARCHIVO_DISTRIBUIDORES, ARCHIVO_TIENDAS


class ToolError(Exception):
    """Error controlado de herramienta; el mensaje se devuelve al modelo."""


def _cargar_tiendas() -> list[dict[str, Any]]:
    try:
        with open(ARCHIVO_TIENDAS, encoding="utf-8") as f:
            return json.load(f)["productos"]
    except FileNotFoundError:
        raise ToolError(f"No existe el archivo de tiendas: {ARCHIVO_TIENDAS}")
    except json.JSONDecodeError as e:
        raise ToolError(f"El archivo de tiendas tiene JSON invalido: {e}")


def _cargar_distribuidores() -> list[dict[str, Any]]:
    import csv

    try:
        with open(ARCHIVO_DISTRIBUIDORES, encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        raise ToolError(f"No existe el catalogo de distribuidores: {ARCHIVO_DISTRIBUIDORES}")


def _coincide(texto: str | None, termino: str) -> bool:
    if not texto:
        return False
    patron = re.sub(r"\s+", " ", termino.lower()).strip()
    return patron in re.sub(r"\s+", " ", texto.lower())


def _numero(valor: str | None, campo: str, id_fila: str, obligatorio: bool = True) -> float | None:
    """Convierte un valor del CSV a numero; si es invalido avisa con la fila exacta.

    Los campos de precio pueden quedar vacios (ej. cajas cerradas sin precio detal);
    los campos estructurales (cantidad minima, resenas, stock) son obligatorios.
    """
    if valor is None or str(valor).strip() == "":
        if obligatorio:
            raise ToolError(
                f"Fila {id_fila} del catalogo de distribuidores: el campo '{campo}' esta vacio. "
                "Corrige el CSV antes de consultar."
            )
        return None
    try:
        return float(valor)
    except ValueError:
        raise ToolError(
            f"Fila {id_fila} del catalogo de distribuidores: el campo '{campo}' no es numerico "
            f"(valor: '{valor}'). Corrige el CSV antes de consultar."
        )


# ---------------------------------------------------------------------------
# Herramienta 1: buscar productos en tiendas online (retail)
# ---------------------------------------------------------------------------
def buscar_en_tiendas(consulta: str, marca: str = "", tipo: str = "") -> dict[str, Any]:
    """Busca productos en el listado capturado de tiendas online.

    Args:
        consulta: texto libre a buscar en nombre/descripcion/beneficios.
        marca: filtra por marca exacta o parcial (opcional).
        tipo: categoria del producto, ej: labial, base, rimel (opcional).
    """
    productos = _cargar_tiendas()
    resultados = []
    for p in productos:
        campos = " ".join(
            str(p.get(c) or "") for c in ("nombre", "descripcion", "beneficios", "marca", "tipo", "tono")
        )
        if not _coincide(campos, consulta):
            continue
        if marca and not _coincide(p.get("marca"), marca):
            continue
        if tipo and not _coincide(str(p.get("tipo")), tipo):
            continue
        resultados.append(p)

    return {
        "total_encontrados": len(resultados),
        "nota": "disponible=false significa producto agotado; se incluye para informar al usuario.",
        "productos": resultados,
    }


# ---------------------------------------------------------------------------
# Herramienta 2: consultar catalogo de distribuidores mayoristas
# ---------------------------------------------------------------------------
def consultar_distribuidores(tipo: str = "", marca: str = "", consulta: str = "") -> dict[str, Any]:
    """Consulta precios detallista y mayorista del catalogo de distribuidores.

    Args:
        tipo: categoria del producto, ej: labial, base, rimel (opcional).
        marca: marca buscada (opcional).
        consulta: texto libre adicional (opcional).
    """
    filas = _cargar_distribuidores()
    resultados = []
    for fila in filas:
        if tipo and not _coincide(fila.get("tipo"), tipo):
            continue
        if marca and not _coincide(fila.get("marca"), marca):
            continue
        if consulta:
            campos = " ".join(str(v or "") for v in fila.values())
            if not _coincide(campos, consulta):
                continue

        def _entero(campo: str, obligatorio: bool = True) -> float | None:
            valor = _numero(fila.get(campo), campo, fila["id"], obligatorio)
            return None if valor is None else round(valor)

        resultados.append(
            {
                "id": fila["id"],
                "nombre": fila["nombre"],
                "marca": fila["marca"],
                "tipo": fila["tipo"],
                "presentacion": fila["presentacion"],
                "tono": fila["tono"] or None,
                "distribuidor": fila["distribuidor"],
                "ciudad_despacho": fila["ciudad_despacho"],
                "precio_unitario_detal_cop": _numero(fila.get("precio_unitario_detal_cop"), "precio_unitario_detal_cop", fila["id"], obligatorio=False),
                "precio_unitario_mayorista_cop": _numero(fila.get("precio_unitario_mayorista_cop"), "precio_unitario_mayorista_cop", fila["id"], obligatorio=False),
                "cantidad_minima_mayorista": _entero("cantidad_minima_mayorista"),
                "calificacion": _numero(fila.get("calificacion"), "calificacion", fila["id"], obligatorio=False),
                "num_resenas": _entero("num_resenas"),
                "stock_unidades": _entero("stock_unidades"),
                "costo_envio_cop": _numero(fila.get("costo_envio_cop"), "costo_envio_cop", fila["id"], obligatorio=False) or 0.0,
                "beneficios": fila["beneficios"],
            }
        )

    return {
        "total_encontrados": len(resultados),
        "nota": (
            "precio_unitario_mayorista_cop aplica SOLO si la compra alcanza "
            "cantidad_minima_mayorista unidades; si no, aplica precio_unitario_detal_cop."
        ),
        "productos": resultados,
    }


# ---------------------------------------------------------------------------
# Herramienta 3: calcular costo total y unitario efectivo de una opcion
# ---------------------------------------------------------------------------
def calcular_costo(precio_unitario_cop: float, cantidad_unidades: int, costo_envio_cop: float = 0) -> dict[str, Any]:
    """Calcula el costo total de una opcion de compra y su precio unitario efectivo.

    Args:
        precio_unitario_cop: precio por unidad en pesos colombianos.
        cantidad_unidades: numero de unidades a comprar.
        costo_envio_cop: costo de envio estimado (0 si es gratis).
    """
    if cantidad_unidades <= 0:
        raise ToolError("cantidad_unidades debe ser un entero positivo.")
    if precio_unitario_cop < 0 or costo_envio_cop < 0:
        raise ToolError("Los precios no pueden ser negativos.")
    subtotal = precio_unitario_cop * cantidad_unidades
    total = subtotal + costo_envio_cop
    return {
        "subtotal_cop": subtotal,
        "costo_envio_cop": costo_envio_cop,
        "costo_total_cop": total,
        "costo_unitario_efectivo_cop": round(total / cantidad_unidades),
    }


REGISTRO_HERRAMIENTAS = {
    "buscar_en_tiendas": buscar_en_tiendas,
    "consultar_distribuidores": consultar_distribuidores,
    "calcular_costo": calcular_costo,
}
