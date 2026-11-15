"""Servidor web (Flask): entrega la interfaz y la API REST del chatbot.

Ejecutar desde la raíz del repositorio:   python -m backend.app
"""
from __future__ import annotations

from flask import Flask, jsonify, request, send_from_directory

from . import config
from .errores import ErrorMotor
from .servicio import ServicioChatbot


def crear_app(servicio: ServicioChatbot | None = None) -> Flask:
    app = Flask(__name__, static_folder=None)
    app.json.ensure_ascii = False
    servicio = servicio or ServicioChatbot()

    @app.get("/")
    def inicio():
        return send_from_directory(config.RUTA_FRONTEND, "index.html")

    @app.get("/<path:archivo>")
    def estaticos(archivo: str):
        return send_from_directory(config.RUTA_FRONTEND, archivo)

    @app.post("/api/preguntar")
    def preguntar():
        datos = request.get_json(silent=True) or {}
        try:
            resultado = servicio.preguntar(
                datos.get("pregunta"), datos.get("motor", "ambos"), datos.get("historial"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify(resultado)

    @app.get("/api/estado")
    def estado():
        return jsonify(servicio.estado())

    @app.get("/api/conocimiento")
    def conocimiento():
        try:
            return jsonify(servicio.base.datos)
        except ErrorMotor as exc:
            return jsonify({"error": str(exc)}), 503

    return app


if __name__ == "__main__":
    print(f"Chatbot disponible en http://localhost:{config.PUERTO}")
    crear_app().run(host="127.0.0.1", port=config.PUERTO, debug=False)
