"""Configuración central. Se lee desde variables de entorno o desde el archivo .env."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:  # python-dotenv es opcional: si no está, se usan solo las variables de entorno.
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

RAIZ = Path(__file__).resolve().parent.parent
RUTA_PROLOG = RAIZ / "prolog"
RUTA_FRONTEND = RAIZ / "frontend"

if load_dotenv:
    load_dotenv(RAIZ / ".env")

# Proveedores compatibles con la API de OpenAI: (base_url, modelo por defecto)
PROVEEDORES = {
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/", "gemini-3.5-flash"),
    "groq": ("https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    "openai": (None, "gpt-4o-mini"),
    "ollama": ("http://localhost:11434/v1", "llama3.1"),
}


@dataclass(frozen=True)
class ConfigLLM:
    proveedor: str
    base_url: str | None
    modelo: str
    api_key: str | None
    temperatura: float
    max_tokens: int
    timeout: float

    @property
    def configurado(self) -> bool:
        # Ollama corre localmente y no necesita una API key real.
        return bool(self.api_key) or self.proveedor == "ollama"


def cargar_config_llm() -> ConfigLLM:
    proveedor = os.getenv("LLM_PROVEEDOR", "gemini").strip().lower()
    url_defecto, modelo_defecto = PROVEEDORES.get(proveedor, (None, "gpt-4o-mini"))
    return ConfigLLM(
        proveedor=proveedor,
        base_url=os.getenv("LLM_BASE_URL") or url_defecto,
        modelo=os.getenv("LLM_MODELO") or modelo_defecto,
        api_key=os.getenv("LLM_API_KEY") or None,
        temperatura=float(os.getenv("LLM_TEMPERATURA", "0")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "600")),
        timeout=float(os.getenv("LLM_TIMEOUT", "60")),
    )


SWIPL = os.getenv("SWIPL", "swipl")
TIMEOUT_PROLOG = float(os.getenv("TIMEOUT_PROLOG", "15"))
LARGO_MAXIMO_PREGUNTA = 500
PUERTO = int(os.getenv("PUERTO", "5000"))
