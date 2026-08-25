"""Cliente LLM compatible con la API de OpenAI, con manejo de errores por tipo."""
import time

from openai import APIConnectionError, APITimeoutError, AuthenticationError, OpenAI, RateLimitError

from .config import Config

REINTENTOS_TIMEOUT = 3
BACKOFF_RATE_LIMIT = [2, 4, 8]


class ErrorLLM(Exception):
    """Error no recuperable del proveedor LLM."""


class ClienteLLM:
    def __init__(self, config: Config):
        if not config.api_key:
            raise ErrorLLM(
                "Falta OPENAI_API_KEY. Copia .env.example a .env y coloca tu clave "
                "(no se admite clave escrita en el codigo)."
            )
        self.config = config
        self.cliente = OpenAI(base_url=config.base_url, api_key=config.api_key, timeout=60)

    def chat(self, mensajes: list[dict], tools: list[dict] | None = None) -> object:
        """Llama al modelo gestionando timeout y rate limit con reintentos.

        Lanza ErrorLLM si el error es definitivo (credenciales, conexion).
        """
        ultimo_error: Exception | str | None = None

        for intento in range(REINTENTOS_TIMEOUT):
            try:
                return self.cliente.chat.completions.create(
                    model=self.config.modelo,
                    messages=mensajes,
                    tools=tools,
                    temperature=self.config.temperatura,
                )
            except RateLimitError:
                if intento < len(BACKOFF_RATE_LIMIT):
                    time.sleep(BACKOFF_RATE_LIMIT[intento])
                    ultimo_error = "limite de peticiones (rate limit)"
                continue
            except APITimeoutError:
                ultimo_error = f"timeout en el intento {intento + 1}"
                continue
            except AuthenticationError as e:
                raise ErrorLLM(f"Credenciales rechazadas por el proveedor. Verifica OPENAI_API_KEY. Detalle: {e}")
            except APIConnectionError as e:
                raise ErrorLLM(f"No hay conexion con el proveedor LLM ({self.config.base_url}). Detalle: {e}")

        raise ErrorLLM(f"El modelo no respondio tras {REINTENTOS_TIMEOUT} reintentos ({ultimo_error}).")
