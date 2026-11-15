"""Puente entre Python y el chatbot en Prolog (SWI-Prolog).

Cada consulta ejecuta `swipl prolog/main.pl --stdin`. Así, si se modifica la base de
conocimiento (conocimiento.pl) durante la demostración, el cambio se ve de inmediato.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from . import config
from .errores import ErrorMotor, MotorNoConfigurado


class MotorProlog:
    nombre = "prolog"

    def __init__(self, carpeta: Path = config.RUTA_PROLOG, ejecutable: str = config.SWIPL,
                 timeout: float = config.TIMEOUT_PROLOG) -> None:
        self.carpeta = Path(carpeta)
        self.ejecutable = ejecutable
        self.timeout = timeout

    @property
    def disponible(self) -> bool:
        return shutil.which(self.ejecutable) is not None and (self.carpeta / "main.pl").exists()

    def _ejecutar(self, argumentos: list[str], entrada: str | None = None) -> str:
        if not self.disponible:
            raise MotorNoConfigurado(
                f"No se encontró SWI-Prolog ('{self.ejecutable}'). Instálalo y agrégalo al PATH.")
        entorno = {**os.environ, "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
        try:
            proceso = subprocess.run(
                [self.ejecutable, "main.pl", *argumentos],
                input=entrada, capture_output=True, text=True, encoding="utf-8",
                cwd=self.carpeta, timeout=self.timeout, env=entorno,
            )
        except subprocess.TimeoutExpired as exc:
            raise ErrorMotor("Prolog tardó demasiado en responder.") from exc
        if proceso.returncode != 0:
            raise ErrorMotor(f"Prolog terminó con error: {proceso.stderr.strip()[:300]}")
        return proceso.stdout

    def responder(self, pregunta: str) -> str:
        """Devuelve la respuesta del chatbot Prolog a una pregunta en español."""
        respuesta = self._ejecutar(["--stdin"], entrada=pregunta).strip()
        if not respuesta:
            raise ErrorMotor("Prolog no entregó respuesta.")
        return respuesta

    def exportar_conocimiento(self) -> dict:
        """Obtiene la base de conocimiento completa como diccionario (desde conocimiento.pl)."""
        salida = self._ejecutar(["--json"])
        try:
            return json.loads(salida)
        except json.JSONDecodeError as exc:
            raise ErrorMotor("No se pudo leer la base de conocimiento exportada por Prolog.") from exc
