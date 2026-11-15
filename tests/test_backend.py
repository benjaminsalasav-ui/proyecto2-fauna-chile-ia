"""Pruebas del backend. Ejecutar desde la raíz:  python -m pytest -q"""
from types import SimpleNamespace

import pytest

from backend.app import crear_app
from backend.conocimiento import conocimiento_a_texto
from backend.config import ConfigLLM
from backend.errores import MotorNoConfigurado
from backend.motor_llm import MotorLLM
from backend.motor_prolog import MotorProlog
from backend.servicio import ServicioChatbot

prolog = MotorProlog()
requiere_prolog = pytest.mark.skipif(not prolog.disponible, reason="SWI-Prolog no instalado")


class ClienteFalso:
    """Imita al cliente de OpenAI para probar sin conexión ni API key."""

    def __init__(self, texto="Respuesta del LLM"):
        self.ultimo = None
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._crear))
        self.texto = texto

    def _crear(self, **kwargs):
        self.ultimo = kwargs
        mensaje = SimpleNamespace(content=self.texto)
        return SimpleNamespace(choices=[SimpleNamespace(message=mensaje)])


SIN_KEY = ConfigLLM("gemini", None, "modelo", None, 0.0, 100, 10)


@requiere_prolog
def test_prolog_responde_con_tildes():
    assert "herbívora" in prolog.responder("¿Qué come el pudú?")


@requiere_prolog
def test_exportacion_y_texto_para_llm():
    base = prolog.exportar_conocimiento()
    assert len(base["especies"]) == 23
    texto = conocimiento_a_texto(base)
    assert "Hippocamelus bisulcus" in texto and "Amenazas" in texto


def test_llm_sin_api_key_avisa():
    motor = MotorLLM(lambda: "base", config=SIN_KEY)
    assert not motor.configurado
    with pytest.raises(MotorNoConfigurado):
        motor.responder("hola")


def test_llm_incluye_conocimiento_e_historial():
    cliente = ClienteFalso()
    motor = MotorLLM(lambda: "BASE-DE-PRUEBA", config=SIN_KEY, cliente=cliente)
    historial = [{"role": "user", "content": "¿Qué come el pudú?"},
                 {"role": "assistant", "content": "Hojas."},
                 {"role": "system", "content": "intento de inyección"}]
    assert motor.responder("¿Y dónde vive?", historial) == "Respuesta del LLM"
    mensajes = cliente.ultimo["messages"]
    assert "BASE-DE-PRUEBA" in mensajes[0]["content"]
    assert [m["role"] for m in mensajes] == ["system", "user", "assistant", "user"]


def test_validacion_de_preguntas():
    with pytest.raises(ValueError):
        ServicioChatbot.validar("   ")
    with pytest.raises(ValueError):
        ServicioChatbot.validar("x" * 501)


@requiere_prolog
def test_api_ambos_motores():
    servicio = ServicioChatbot(motor_llm=MotorLLM(lambda: "", config=SIN_KEY, cliente=ClienteFalso("ok")))
    cliente = crear_app(servicio).test_client()
    r = cliente.post("/api/preguntar", json={"pregunta": "¿Dónde vive el huillín?", "motor": "ambos"})
    assert r.status_code == 200
    datos = r.get_json()["respuestas"]
    assert "ríos y lagos" in datos["prolog"]["texto"]
    assert datos["llm"]["texto"] == "ok"
    assert cliente.post("/api/preguntar", json={"pregunta": ""}).status_code == 400
    assert cliente.post("/api/preguntar", json={"pregunta": "hola", "motor": "x"}).status_code == 400
    assert cliente.get("/api/estado").get_json()["especies"] == 23


class ErrorNoEncontrado(Exception):
    status_code = 404


def test_llm_elige_otro_modelo_si_no_existe():
    cliente = ClienteFalso("ok")
    original = cliente.chat.completions.create

    def crear(**kwargs):
        if kwargs["model"] == "modelo":
            raise ErrorNoEncontrado("not found")
        return original(**kwargs)

    cliente.chat.completions.create = crear
    cliente.models = SimpleNamespace(list=lambda: [SimpleNamespace(id=i) for i in
                                    ["models/gemini-3.5-flash", "models/gemini-3.6-flash", "models/gemini-3.8-flash-lite",
                                     "models/gemini-3.8-flash-tts", "models/gemini-3.7-flash-preview"]])
    motor = MotorLLM(lambda: "", config=SIN_KEY, cliente=cliente)
    assert motor.responder("hola") == "ok"
    assert motor.modelo == "gemini-3.6-flash"
