"""Configuracion central. Las credenciales SOLO se leen de variables de entorno (.env).

En despliegue (Streamlit Community Cloud) no hay archivo .env: las credenciales se
configuran en el panel Secrets del dashboard y el agente las lee via st.secrets.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ARCHIVO_TIENDAS = DATA_DIR / "tiendas_online.json"
ARCHIVO_DISTRIBUIDORES = DATA_DIR / "catalogo_distribuidores.csv"


@dataclass
class Config:
    base_url: str
    api_key: str
    modelo: str
    temperatura: float


def _valor(nombre: str, por_defecto: str = "") -> str:
    """Lee una credencial: 1) variable de entorno (.env local), 2) st.secrets (nube)."""
    valor = os.getenv(nombre, "")
    if valor:
        return valor
    try:
        import streamlit as st

        return st.secrets.get(nombre, por_defecto)
    except Exception:
        return por_defecto


def cargar_config() -> Config:
    load_dotenv(BASE_DIR / ".env")
    return Config(
        base_url=_valor("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"),
        api_key=_valor("OPENAI_API_KEY"),
        modelo=_valor("LLM_MODEL", "gemini-2.0-flash"),
        temperatura=float(_valor("LLM_TEMPERATURE", "0.2")),
    )
