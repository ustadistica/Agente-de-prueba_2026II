"""Configuracion central. Las credenciales SOLO se leen de variables de entorno (.env)."""
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


def cargar_config() -> Config:
    load_dotenv(BASE_DIR / ".env")
    return Config(
        base_url=os.getenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        modelo=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
        temperatura=float(os.getenv("LLM_TEMPERATURE", "0.2")),
    )
