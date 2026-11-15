"""Excepciones propias del sistema."""


class ErrorMotor(Exception):
    """Error al obtener una respuesta de un motor (Prolog o LLM)."""


class MotorNoConfigurado(ErrorMotor):
    """El motor no puede usarse porque falta configuración (p. ej. la API key del LLM)."""
