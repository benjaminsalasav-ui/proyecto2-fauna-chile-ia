"""Evalúa ambos chatbots con las 20 preguntas de preguntas.json.

Uso (desde la raíz del repositorio):
    python -m evaluacion.evaluar            # Prolog + LLM (si está configurado en .env)
    python -m evaluacion.evaluar --solo-prolog

Genera:
    (Además evalúa evaluacion/preguntas_robustez.json: 10 preguntas extra no usadas para ajustar el sistema.)
    evaluacion/resultados.json   respuestas, tiempos y evaluación de cada pregunta
    evaluacion/resultados.md     tabla legible
    informe/Informe_Proyecto2_Entrega2.docx   (vía informe/generar_informe.py)

Criterio automático (sobre el texto sin tildes y en minúsculas):
    correcta   = contiene todos los elementos esperados y ninguno prohibido
    parcial    = contiene parte de lo esperado, o todo pero también algo prohibido
    incorrecta = no contiene nada de lo esperado
"""
from __future__ import annotations

import argparse
import json
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from backend.errores import ErrorMotor
from backend.servicio import ServicioChatbot

CARPETA = Path(__file__).resolve().parent
PUNTAJE = {"correcta": 1.0, "parcial": 0.5, "incorrecta": 0.0, "sin respuesta": 0.0}


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")


def evaluar_respuesta(texto: str | None, esperado: list, prohibido: list) -> dict:
    if not texto:
        return {"estado": "sin respuesta", "cumplidos": 0, "total": len(esperado), "prohibidos": []}
    t = normalizar(texto)
    cumplidos = sum(
        1 for criterio in esperado
        if any(alt in t for alt in (criterio if isinstance(criterio, list) else [criterio]))
    )
    encontrados = [p for p in prohibido if p in t]
    if cumplidos == len(esperado) and not encontrados:
        estado = "correcta"
    elif cumplidos > 0:
        estado = "parcial"
    else:
        estado = "incorrecta"
    return {"estado": estado, "cumplidos": cumplidos, "total": len(esperado), "prohibidos": encontrados}


def evaluar_conjunto(servicio: ServicioChatbot, archivo: str, usar_llm: bool) -> list:
    preguntas = json.loads((CARPETA / archivo).read_text(encoding="utf-8"))
    filas = []
    for p in preguntas:
        fila = {k: p[k] for k in ("id", "categoria", "pregunta", "esperado", "prohibido")}
        motores = ["prolog"] + (["llm"] if usar_llm else [])
        for motor in motores:
            r = servicio.preguntar(p["pregunta"], motor)["respuestas"][motor]
            r["evaluacion"] = evaluar_respuesta(r["texto"], p["esperado"], p["prohibido"])
            fila[motor] = r
            print(f"[{p['id']:>2}] {motor:<6} {r['evaluacion']['estado']:<13} {r['ms']:>5} ms  {p['pregunta']}")
        filas.append(fila)
        if usar_llm:
            time.sleep(1)  # evita superar el límite de solicitudes por minuto del plan gratuito
    return filas


def ejecutar(solo_prolog: bool = False) -> dict:
    servicio = ServicioChatbot()
    usar_llm = servicio.llm.configurado and not solo_prolog
    motores = ["prolog", "llm"] if usar_llm else ["prolog"]
    print("== Set principal (20 preguntas) ==")
    filas = evaluar_conjunto(servicio, "preguntas.json", usar_llm)
    print("== Set complementario de robustez (10 preguntas no usadas para ajustar el sistema) ==")
    robustez = evaluar_conjunto(servicio, "preguntas_robustez.json", usar_llm)
    return {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "llm": {"usado": usar_llm, "proveedor": servicio.llm.config.proveedor, "modelo": servicio.llm.config.modelo},
        "preguntas": filas,
        "resumen": {m: resumir(filas, m) for m in motores},
        "robustez": robustez,
        "resumen_robustez": {m: resumir(robustez, m) for m in motores},
    }


def resumir(filas: list, motor: str) -> dict:
    estados = [f[motor]["evaluacion"]["estado"] for f in filas]
    tiempos = [f[motor]["ms"] for f in filas if f[motor]["texto"]]
    return {
        "correctas": estados.count("correcta"),
        "parciales": estados.count("parcial"),
        "incorrectas": estados.count("incorrecta"),
        "sin_respuesta": estados.count("sin respuesta"),
        "puntaje": sum(PUNTAJE[e] for e in estados),
        "total": len(estados),
        "tiempo_promedio_ms": round(sum(tiempos) / len(tiempos)) if tiempos else None,
    }


def escribir_markdown(resultado: dict) -> str:
    motores = list(resultado["resumen"])
    lineas = [f"# Resultados de la evaluación ({resultado['fecha']})", ""]
    for m in motores:
        r = resultado["resumen"][m]
        lineas.append(f"- **{m}**: {r['correctas']} correctas, {r['parciales']} parciales, "
                      f"{r['incorrectas']} incorrectas, puntaje {r['puntaje']}/{r['total']}, "
                      f"tiempo promedio {r['tiempo_promedio_ms']} ms")
    lineas += ["", "| # | Pregunta | " + " | ".join(motores) + " |",
               "|---|---|" + "---|" * len(motores)]
    for f in resultado["preguntas"]:
        celdas = [f"**{f[m]['evaluacion']['estado']}**: " + (f[m]["texto"] or f[m]["error"] or "").replace("\n", " ").replace("|", "/")
                  for m in motores]
        lineas.append(f"| {f['id']} | {f['pregunta']} | " + " | ".join(celdas) + " |")
    lineas += ["", "## Set complementario de robustez", ""]
    for m in motores:
        r = resultado["resumen_robustez"][m]
        lineas.append(f"- **{m}**: {r['correctas']} correctas, {r['parciales']} parciales, "
                      f"{r['incorrectas']} incorrectas, puntaje {r['puntaje']}/{r['total']}")
    lineas += ["", "| # | Pregunta | " + " | ".join(motores) + " |", "|---|---|" + "---|" * len(motores)]
    for f in resultado["robustez"]:
        celdas = [f"**{f[m]['evaluacion']['estado']}**: " + (f[m]["texto"] or f[m]["error"] or "").replace("|", "/")
                  for m in motores]
        lineas.append(f"| {f['id']} | {f['pregunta']} | " + " | ".join(celdas) + " |")
    return "\n".join(lineas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--solo-prolog", action="store_true", help="no consultar el LLM")
    parser.add_argument("--sin-informe", action="store_true", help="no regenerar el informe Word")
    args = parser.parse_args()
    try:
        resultado = ejecutar(args.solo_prolog)
    except ErrorMotor as exc:
        raise SystemExit(f"Error: {exc}")
    if not resultado["llm"]["usado"] and not args.solo_prolog:
        print("\nAVISO: el LLM no está configurado (.env), solo se evaluó Prolog.")
    (CARPETA / "resultados.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    (CARPETA / "resultados.md").write_text(escribir_markdown(resultado), encoding="utf-8")
    print("\nResumen:", json.dumps(resultado["resumen"], ensure_ascii=False))
    print("Robustez:", json.dumps(resultado["resumen_robustez"], ensure_ascii=False))
    if not args.sin_informe:
        from informe.generar_informe import generar
        ruta = generar(resultado)
        print(f"Informe generado: {ruta}")


if __name__ == "__main__":
    main()
