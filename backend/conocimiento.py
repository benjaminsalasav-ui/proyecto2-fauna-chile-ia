"""Base de conocimiento compartida.

La fuente única de verdad es prolog/conocimiento.pl. Este módulo la exporta (vía Prolog),
la guarda en caché mientras el archivo no cambie y la convierte en texto para el LLM.
"""
from __future__ import annotations

from pathlib import Path

from .motor_prolog import MotorProlog


def _si_no(valor: bool) -> str:
    return "sí" if valor else "no"


def _lista(valores: list[str]) -> str:
    return ", ".join(valores) if valores else "sin registro"


def especie_a_texto(e: dict) -> str:
    lineas = [
        f"### {e['nombre']} ({e['nombre_cientifico']})",
        f"- Otros nombres: {_lista(e['otros_nombres'])}",
        f"- Clase: {e['clase']}",
        f"- Dieta: {e['dieta']}; se alimenta de: {_lista(e['alimentos'])}",
        f"- Ecosistemas: {_lista(e['ecosistemas'])}",
        f"- Zonas de Chile: {_lista(e['zonas'])}",
        f"- Localidades donde se puede observar: {_lista(e['localidades'])}",
        f"- Estado de conservación (UICN): {e['estado_conservacion']}; amenazada: {_si_no(e['amenazada'])}",
        f"- Endémica de Chile: {_si_no(e['endemica_chile'])}",
        f"- Amenazas: {_lista(e['amenazas'])}",
        f"- Presas que también están en la base: {_lista(e['presas_en_la_base'])}",
        f"- Depredadores que también están en la base: {_lista(e['depredadores_en_la_base'])}",
        f"- Aparece en el escudo nacional: {_si_no(e['emblema_nacional'])}",
    ]
    if e.get("dato_curioso"):
        lineas.append(f"- Dato curioso: {e['dato_curioso']}")
    return "\n".join(lineas)


def conocimiento_a_texto(base: dict) -> str:
    cabecera = [
        f"Fuente: {base.get('fuente', '')}",
        f"Zonas: {base.get('zonas', '')}",
        "Definiciones: 'amenazada' = estado VU, EN o CR; 'en peligro' = estado EN o CR.",
        f"Total de especies en la base: {len(base['especies'])}.",
        "",
    ]
    return "\n".join(cabecera) + "\n\n".join(especie_a_texto(e) for e in base["especies"])


class BaseConocimiento:
    """Carga la base desde Prolog y la recarga solo si conocimiento.pl cambió."""

    def __init__(self, motor: MotorProlog) -> None:
        self.motor = motor
        self._archivo = Path(motor.carpeta) / "conocimiento.pl"
        self._marca: float | None = None
        self._datos: dict | None = None
        self._texto: str = ""

    def _actualizar(self) -> None:
        marca = self._archivo.stat().st_mtime
        if self._datos is None or marca != self._marca:
            self._datos = self.motor.exportar_conocimiento()
            self._texto = conocimiento_a_texto(self._datos)
            self._marca = marca

    @property
    def datos(self) -> dict:
        self._actualizar()
        return self._datos

    @property
    def texto(self) -> str:
        self._actualizar()
        return self._texto
