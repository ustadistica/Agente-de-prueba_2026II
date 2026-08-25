"""Modelos de datos y contrato de salida estructurada del agente."""
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class ItemFuente(BaseModel):
    fuente: Literal["tienda_online", "distribuidor"]
    id: str


class GrupoEquivalente(BaseModel):
    nombre_canonico: str
    marca: str
    items: list[ItemFuente]


class OpcionComparada(BaseModel):
    grupo: str
    referencia_fuente_id: str
    proveedor: str
    modalidad: Literal["detal", "mayorista"]
    precio_unitario_cop: int
    cantidad_minima: int
    unidades_a_comprar: int
    costo_envio_cop: float
    costo_total_cop: float
    costo_unitario_efectivo_cop: float
    calificacion: Optional[float] = None
    ciudad_despacho: str
    ventajas: list[str] = []
    limitaciones: list[str] = []


class Recomendacion(BaseModel):
    opcion_ganadora_id: str
    criterio_aplicado: str
    justificacion: str
    alternativa_sugerida: str
    alertas: list[str] = []


class SalidaAgente(BaseModel):
    interpretacion_consulta: str
    grupos_equivalentes: list[GrupoEquivalente]
    comparativo: list[OpcionComparada]
    recomendacion: Recomendacion
    datos_insuficientes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def ganadora_debe_existir_en_comparativo(self) -> "SalidaAgente":
        ids = {o.referencia_fuente_id for o in self.comparativo}
        if ids and self.recomendacion.opcion_ganadora_id not in ids:
            raise ValueError(
                f"opcion_ganadora_id '{self.recomendacion.opcion_ganadora_id}' no corresponde a "
                "ninguna referencia_fuente_id del comparativo. Usa uno de: " + ", ".join(sorted(ids))
            )
        return self
