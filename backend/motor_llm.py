"""Chatbot basado en un LLM (Large Language Model).

El LLM no responde "de memoria": recibe en el mensaje de sistema toda la base de
conocimiento del proyecto (la misma que usa Prolog) y la instrucción de responder solo
con esa información (técnica de *grounding* o generación aumentada con contexto).

Funciona con cualquier proveedor compatible con la API de OpenAI: Gemini, Groq,
OpenAI u Ollama (local). Se configura en el archivo .env.
"""
from __future__ import annotations

import re
import time
from typing import Callable, Iterable

from .config import ConfigLLM, cargar_config_llm
from .errores import ErrorMotor, MotorNoConfigurado

PROMPT_SISTEMA = """Eres un chatbot que responde preguntas sobre la fauna nativa de Chile.
Responde en español, de forma clara y breve (máximo 5 oraciones; usa una lista solo si te piden varias especies).

Reglas obligatorias:
1. Usa ÚNICAMENTE la información de la BASE DE CONOCIMIENTO de abajo. No agregues datos externos ni inventes.
2. Si la respuesta no está en la base, dilo explícitamente con la frase "No tengo esa información en mi base de conocimiento" y sugiere una pregunta que sí puedas responder.
3. Si la pregunta no trata sobre fauna nativa de Chile, responde que solo puedes hablar de ese tema.
4. Cuando te pidan una lista de especies, incluye todas las que cumplen la condición y ninguna otra. Si te piden contar, entrega el número exacto.
5. "Amenazada" significa estado VU, EN o CR. "En peligro" significa EN o CR.
6. Tolera errores de ortografía en los nombres de las especies (por ejemplo "guemul" es "huemul").

BASE DE CONOCIMIENTO:
{conocimiento}"""

MAX_TURNOS_HISTORIAL = 6
REINTENTOS_CUOTA = 2      # reintentos si el proveedor responde 429 (límite por minuto)
ESPERA_CUOTA_S = 20
_EXCLUIR = ("lite", "tts", "live", "audio", "image", "embedding", "vision", "robotics",
            "transcribe", "omni", "translate", "aqa", "learnlm", "gemma", "thinking")


def _clave_version(modelo: str) -> tuple:
    return tuple(int(n) for n in re.findall(r"\d+", modelo)[:3])


class MotorLLM:
    nombre = "llm"

    def __init__(self, proveedor_conocimiento: Callable[[], str],
                 config: ConfigLLM | None = None, cliente=None) -> None:
        """
        proveedor_conocimiento: función que devuelve la base de conocimiento en texto.
        cliente: cliente compatible con OpenAI (se puede inyectar uno falso en las pruebas).
        """
        self._conocimiento = proveedor_conocimiento
        self.config = config or cargar_config_llm()
        self._cliente = cliente
        self.modelo = self.config.modelo  # puede cambiar si el modelo configurado no existe

    @property
    def configurado(self) -> bool:
        return self._cliente is not None or self.config.configurado

    def _obtener_cliente(self):
        if self._cliente is None:
            if not self.config.configurado:
                raise MotorNoConfigurado(
                    "El LLM no está configurado: define LLM_API_KEY (y LLM_PROVEEDOR) en el archivo .env.")
            try:
                from openai import OpenAI
            except ImportError as exc:  # pragma: no cover
                raise MotorNoConfigurado("Falta el paquete 'openai' (pip install -r requirements.txt).") from exc
            self._cliente = OpenAI(api_key=self.config.api_key or "ollama",
                                   base_url=self.config.base_url, timeout=self.config.timeout)
        return self._cliente

    def construir_mensajes(self, pregunta: str, historial: Iterable[dict] | None = None) -> list[dict]:
        mensajes = [{"role": "system", "content": PROMPT_SISTEMA.format(conocimiento=self._conocimiento())}]
        for turno in list(historial or [])[-MAX_TURNOS_HISTORIAL:]:
            if turno.get("role") in ("user", "assistant") and isinstance(turno.get("content"), str):
                mensajes.append({"role": turno["role"], "content": turno["content"][:2000]})
        mensajes.append({"role": "user", "content": pregunta})
        return mensajes

    def _elegir_modelo_disponible(self, cliente) -> str | None:
        """Si el modelo configurado no existe, busca el modelo 'flash' estable más reciente de la cuenta."""
        try:
            ids = [m.id.split("/")[-1] for m in cliente.models.list()]
        except Exception:
            return None
        candidatos = [i for i in ids if "flash" in i and not any(x in i for x in _EXCLUIR)]
        estables = [i for i in candidatos if "preview" not in i and "exp" not in i] or candidatos
        return max(estables, key=_clave_version) if estables else None

    def _crear(self, cliente, mensajes: list[dict]):
        for intento in range(REINTENTOS_CUOTA + 1):
            try:
                return cliente.chat.completions.create(
                    model=self.modelo, messages=mensajes,
                    temperature=self.config.temperatura, max_tokens=self.config.max_tokens,
                )
            except Exception as exc:
                if getattr(exc, "status_code", None) != 429 or intento == REINTENTOS_CUOTA:
                    raise
                time.sleep(ESPERA_CUOTA_S)

    def responder(self, pregunta: str, historial: Iterable[dict] | None = None) -> str:
        cliente = self._obtener_cliente()
        mensajes = self.construir_mensajes(pregunta, historial)
        try:
            try:
                respuesta = self._crear(cliente, mensajes)
            except Exception as exc:
                if getattr(exc, "status_code", None) != 404:
                    raise
                nuevo = self._elegir_modelo_disponible(cliente)
                if not nuevo or nuevo == self.modelo:
                    raise
                self.modelo = nuevo
                respuesta = self._crear(cliente, mensajes)
        except Exception as exc:  # errores de red, cuota, modelo inexistente, etc.
            raise ErrorMotor(f"Error al consultar el LLM ({self.config.proveedor}, modelo {self.modelo}): {exc}") from exc
        eleccion = respuesta.choices[0]
        texto = (eleccion.message.content or "").strip()
        if not texto:
            raise ErrorMotor("El LLM devolvió una respuesta vacía.")
        if getattr(eleccion, "finish_reason", None) == "length":
            texto += " […respuesta cortada por el límite de longitud]"
        return texto
