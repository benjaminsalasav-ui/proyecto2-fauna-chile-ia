"""Capa de servicio: valida la pregunta, consulta los motores y mide el tiempo de respuesta."""
from __future__ import annotations

import time
from dataclasses import asdict, dataclass

from . import config
from .conocimiento import BaseConocimiento
from .errores import ErrorMotor
from .motor_llm import MotorLLM
from .motor_prolog import MotorProlog

MOTORES_VALIDOS = ("prolog", "llm", "ambos")


@dataclass
class Resultado:
    motor: str
    texto: str | None
    ms: int
    error: str | None = None

    def a_dict(self) -> dict:
        return asdict(self)


class ServicioChatbot:
    def __init__(self, motor_prolog: MotorProlog | None = None, motor_llm: MotorLLM | None = None) -> None:
        self.prolog = motor_prolog or MotorProlog()
        self.base = BaseConocimiento(self.prolog)
        self.llm = motor_llm or MotorLLM(lambda: self.base.texto)

    @staticmethod
    def validar(pregunta: object) -> str:
        if not isinstance(pregunta, str) or not pregunta.strip():
            raise ValueError("La pregunta no puede estar vacía.")
        pregunta = pregunta.strip()
        if len(pregunta) > config.LARGO_MAXIMO_PREGUNTA:
            raise ValueError(f"La pregunta supera los {config.LARGO_MAXIMO_PREGUNTA} caracteres.")
        return pregunta

    def _consultar(self, nombre: str, funcion, *args) -> Resultado:
        inicio = time.perf_counter()
        try:
            texto, error = funcion(*args), None
        except ErrorMotor as exc:
            texto, error = None, str(exc)
        return Resultado(nombre, texto, int((time.perf_counter() - inicio) * 1000), error)

    def preguntar(self, pregunta: str, motor: str = "ambos", historial: list | None = None) -> dict:
        pregunta = self.validar(pregunta)
        if motor not in MOTORES_VALIDOS:
            raise ValueError(f"Motor inválido: usa uno de {', '.join(MOTORES_VALIDOS)}.")
        resultados = {}
        if motor in ("prolog", "ambos"):
            resultados["prolog"] = self._consultar("prolog", self.prolog.responder, pregunta).a_dict()
        if motor in ("llm", "ambos"):
            resultados["llm"] = self._consultar("llm", self.llm.responder, pregunta, historial).a_dict()
        return {"pregunta": pregunta, "respuestas": resultados}

    def estado(self) -> dict:
        try:
            especies = len(self.base.datos["especies"])
        except ErrorMotor:
            especies = 0
        return {
            "prolog": self.prolog.disponible,
            "llm": self.llm.configurado,
            "proveedor_llm": self.llm.config.proveedor,
            "modelo_llm": self.llm.modelo,
            "especies": especies,
        }
