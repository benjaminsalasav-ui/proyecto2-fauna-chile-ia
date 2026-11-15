"""Genera el informe Word de la Entrega 2 a partir de evaluacion/resultados.json.

Uso (desde la raíz):  python -m informe.generar_informe
(evaluacion/evaluar.py lo llama automáticamente al terminar.)
"""
from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "informe" / "Informe_Proyecto2_Entrega2.docx"
VERDE = RGBColor(0x2F, 0x6B, 0x4F)
COLOR_ESTADO = {"correcta": "D9EAD3", "parcial": "FFF2CC", "incorrecta": "F4CCCC", "sin respuesta": "EEEEEE"}
INTEGRANTES = ["Benjamín Salas", "Luis Romero", "Matías Vicencio"]

# ----------------------------------------------------------------- utilidades

def sombrear(celda, color_hex: str) -> None:
    tc_pr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def repetir_encabezado(fila) -> None:
    tr_pr = fila._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    tr_pr.append(el)


def tabla(doc, encabezados, filas, anchos_cm, tam=9, colores=None):
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, texto in enumerate(encabezados):
        c = t.rows[0].cells[i]
        c.text = ""
        run = c.paragraphs[0].add_run(texto)
        run.bold, run.font.size = True, Pt(tam)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        sombrear(c, "2F6B4F")
    repetir_encabezado(t.rows[0])
    for r, fila in enumerate(filas):
        celdas = t.add_row().cells
        for i, valor in enumerate(fila):
            celdas[i].text = ""
            parrafo = celdas[i].paragraphs[0]
            agregar_texto_con_negrita(parrafo, str(valor), tam)
            if colores and colores[r] and colores[r][i]:
                sombrear(celdas[i], colores[r][i])
    t.autofit = False
    grid = t._tbl.tblGrid
    for i, ancho in enumerate(anchos_cm):
        t.columns[i].width = Cm(ancho)
        grid.gridCol_lst[i].w = Cm(ancho)
    for fila in t.rows:
        for i, ancho in enumerate(anchos_cm):
            fila.cells[i].width = Cm(ancho)
    doc.add_paragraph()
    return t


def agregar_texto_con_negrita(parrafo, texto: str, tam=None):
    """Interpreta **negrita** dentro del texto."""
    partes = texto.split("**")
    for i, parte in enumerate(partes):
        if parte:
            run = parrafo.add_run(parte)
            run.bold = i % 2 == 1
            if tam:
                run.font.size = Pt(tam)


def p(doc, texto: str, estilo=None):
    parrafo = doc.add_paragraph(style=estilo)
    agregar_texto_con_negrita(parrafo, texto)
    return parrafo


def viñetas(doc, items):
    for item in items:
        p(doc, item, "List Bullet")


def codigo(doc, texto: str):
    for linea in texto.strip("\n").split("\n"):
        par = doc.add_paragraph()
        par.paragraph_format.space_after = Pt(0)
        par.paragraph_format.left_indent = Cm(0.6)
        run = par.add_run(linea or " ")
        run.font.name, run.font.size = "Consolas", Pt(9)
    doc.add_paragraph()


def configurar_estilos(doc):
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(11)
    normal.paragraph_format.space_after = Pt(6)
    for nivel, tam in ((1, 15), (2, 12.5), (3, 11.5)):
        e = doc.styles[f"Heading {nivel}"]
        e.font.name, e.font.size, e.font.bold = "Calibri", Pt(tam), True
        e.font.color.rgb = VERDE
        e.paragraph_format.space_before = Pt(14 if nivel == 1 else 10)
        e.paragraph_format.space_after = Pt(6)
        e.paragraph_format.keep_with_next = True
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.2)
        s.top_margin = s.bottom_margin = Cm(2.2)


def numero_pagina(doc):
    par = doc.sections[0].footer.paragraphs[0]
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = par.add_run()
    for tipo, texto in (("begin", None), (None, "PAGE"), ("end", None)):
        if tipo:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tipo)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = texto
        run._r.append(el)

# ------------------------------------------------------------- texto dinámico

def lista_ids(filas, motor, estados):
    return [str(f["id"]) for f in filas if f[motor]["evaluacion"]["estado"] in estados]


def frase_resumen(nombre, r):
    return (f"**{nombre}:** {r['correctas']} correctas, {r['parciales']} parciales y "
            f"{r['incorrectas'] + r['sin_respuesta']} incorrectas (puntaje {r['puntaje']:g}/{r['total']}), "
            f"con un tiempo promedio de respuesta de {r['tiempo_promedio_ms']} ms.")


def celda_respuesta(f, motor):
    if motor not in f:
        return "Pendiente: ejecutar python -m evaluacion.evaluar con el LLM configurado."
    r = f[motor]
    texto = r["texto"] or f"[Error] {r['error']}"
    return f"**{r['evaluacion']['estado'].upper()}** · {texto}"


def color_fila(f, motores):
    return [None, None] + [COLOR_ESTADO.get(f[m]["evaluacion"]["estado"]) if m in f else "EEEEEE" for m in motores]

# --------------------------------------------------------------------- informe

def generar(resultado: dict | None = None) -> Path:
    if resultado is None:
        resultado = json.loads((RAIZ / "evaluacion" / "resultados.json").read_text(encoding="utf-8"))
    llm_usado = resultado["llm"]["usado"]
    modelo = f"{resultado['llm']['modelo']} ({resultado['llm']['proveedor']})"
    filas, robustez = resultado["preguntas"], resultado.get("robustez", [])
    rp, rr = resultado["resumen"], resultado.get("resumen_robustez", {})

    doc = Document()
    configurar_estilos(doc)
    numero_pagina(doc)

    # Portada
    for _ in range(5):
        doc.add_paragraph()
    for texto, tam, negrita in (("Universidad Andrés Bello · Ingeniería Civil Informática", 12, False),
                                ("Fundamentos de Inteligencia Artificial", 12, False),
                                ("Proyecto N°2 — Entrega 2", 22, True),
                                ("Chatbot de fauna nativa de Chile con lógica de primer orden (Prolog) y con un LLM", 14, False),
                                ("Informe de análisis de desempeño", 13, True)):
        par = doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = par.add_run(texto)
        run.font.size, run.bold = Pt(tam), negrita
        if negrita:
            run.font.color.rgb = VERDE
    for _ in range(5):
        doc.add_paragraph()
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.add_run("Integrantes: " + ", ".join(INTEGRANTES)).font.size = Pt(11)
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    par.add_run("Fecha de entrega: domingo 15 de noviembre de 2026").font.size = Pt(11)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # 1. Introducción
    doc.add_heading("1. Introducción", 1)
    p(doc, "Este informe corresponde a la segunda entrega del Proyecto N°2. En la primera entrega se eligió el dominio, "
           "se modeló el conocimiento en lógica de primer orden y se construyó un chatbot en Prolog. En esta entrega se "
           "completa el sistema con los puntos 4, 5 y 6 del enunciado:")
    viñetas(doc, [
        "**Chatbot con un LLM en Python** que responde usando el mismo conocimiento recopilado.",
        "**Interfaz web simple** que funciona como frontend de ambos chatbots y permite compararlos lado a lado.",
        "**Evaluación de desempeño** con 20 preguntas del dominio, análisis, fortalezas y debilidades de cada versión y propuestas de mejora.",
    ])
    p(doc, "Todo el código está versionado en el repositorio git del proyecto (carpetas prolog/, backend/, frontend/, "
           "evaluacion/ e informe/). El archivo README.md explica cómo instalarlo y ejecutarlo.")

    # 2. Dominio
    doc.add_heading("2. Dominio seleccionado: fauna nativa de Chile", 1)
    p(doc, "El chatbot responde preguntas sobre la fauna nativa de Chile: qué come cada especie, dónde vive, su estado de "
           "conservación, sus amenazas, si es endémica, quién la depreda y datos curiosos. Elegimos este dominio porque "
           "no está relacionado con la informática, es de interés público (educación ambiental y turismo), tiene "
           "información verificable en fuentes oficiales como la Lista Roja de la UICN y se presta naturalmente para "
           "relaciones lógicas: clasificaciones, ubicación geográfica, cadenas alimentarias y categorías de riesgo.")
    p(doc, "La base de conocimiento incluye **23 especies**: 14 mamíferos (por ejemplo huemul, pudú, puma, zorro de Darwin, "
           "huillín y chungungo), 7 aves (cóndor andino, pingüino de Humboldt, flamenco chileno, ñandú, entre otras) y "
           "2 anfibios (ranita de Darwin y rana grande chilena). Los estados de conservación usan las categorías de la "
           "Lista Roja de la UICN (LC, NT, VU, EN, CR).")

    # 3. Modelo LPO
    doc.add_heading("3. Modelo de conocimiento en lógica de primer orden", 1)
    p(doc, "El dominio del discurso son las especies y sus atributos. Las constantes son los identificadores de especie "
           "(huemul, pudu, condor…), las clases, zonas, ecosistemas, estados y alimentos. La base de conocimiento "
           "(prolog/conocimiento.pl) es la **única fuente de verdad**: Prolog la consulta directamente y el LLM la recibe "
           "exportada a texto, por lo que ambas versiones responden con exactamente el mismo conocimiento.")
    tabla(doc, ["Predicado", "Significado", "Ejemplo"], [
        ["especie(E, Nombre, Científico)", "E es una especie con ese nombre común y científico", "especie(huemul, 'huemul', 'Hippocamelus bisulcus')"],
        ["clase(E, C)", "E pertenece a la clase C", "clase(condor, ave)"],
        ["dieta(E, D) / come(E, A)", "Tipo de dieta de E / E se alimenta de A", "come(puma, guanaco)"],
        ["ecosistema(E, H) / zona(E, Z)", "E habita el ecosistema H / la zona Z de Chile", "zona(vicuna, norte)"],
        ["conservacion(E, S)", "Estado UICN de E", "conservacion(huillin, en)"],
        ["endemica_chile(E)", "E solo vive en Chile", "endemica_chile(degu)"],
        ["localidad(E, L)", "E se puede observar en L", "localidad(zorro_darwin, chiloe)"],
        ["amenaza(E, T) / dato_curioso(E, T)", "Amenaza o dato curioso de E", "amenaza(condor, 'envenenamiento…')"],
        ["emblema_nacional(E)", "E aparece en el escudo de Chile", "emblema_nacional(huemul)"],
    ], [4.6, 5.6, 6.4])
    p(doc, "Reglas (conocimiento derivado):")
    codigo(doc, """
∀x (conservacion(x, s) ∧ s ∈ {VU, EN, CR} → amenazada(x))
∀x (conservacion(x, s) ∧ s ∈ {EN, CR} → en_peligro(x))
∀p ∀x (come(p, x) ∧ especie(x) → depredador_de(p, x))
∀x ∀y (∃h (ecosistema(x, h) ∧ ecosistema(y, h)) ∧ x ≠ y → comparten_habitat(x, y))

amenazada(X)   :- conservacion(X, S), memberchk(S, [vu, en, cr]).
en_peligro(X)  :- conservacion(X, S), memberchk(S, [en, cr]).
depredador_de(P, X) :- come(P, X), especie(X, _, _).
comparten_habitat(X, Y) :- ecosistema(X, H), ecosistema(Y, H), X \\= Y.""")

    # 4. Arquitectura
    doc.add_heading("4. Arquitectura del sistema", 1)
    tabla(doc, ["Componente", "Archivo(s)", "Responsabilidad"], [
        ["Base de conocimiento", "prolog/conocimiento.pl", "Hechos y reglas en lógica de primer orden"],
        ["Chatbot Prolog", "prolog/chatbot.pl, prolog/main.pl", "Entiende la pregunta, consulta la base y redacta la respuesta"],
        ["Puente Python–Prolog", "backend/motor_prolog.py", "Ejecuta SWI-Prolog y exporta la base en JSON"],
        ["Base compartida", "backend/conocimiento.py", "Convierte la base a texto para el LLM y la recarga si el archivo cambia"],
        ["Chatbot LLM", "backend/motor_llm.py", "Arma el prompt con la base de conocimiento y consulta el modelo"],
        ["Servicio y API", "backend/servicio.py, backend/app.py", "Valida, mide tiempos y expone /api/preguntar, /api/estado, /api/conocimiento"],
        ["Interfaz web", "frontend/index.html, app.js, styles.css", "Chat con modos Prolog, LLM y comparación lado a lado"],
        ["Evaluación", "evaluacion/evaluar.py, preguntas.json", "Ejecuta las 20 preguntas, califica y genera este informe"],
        ["Pruebas", "prolog/tests/, tests/", "20 pruebas en Prolog (plunit) y 6 en Python (pytest)"],
    ], [3.6, 5.6, 7.4])
    p(doc, "Flujo de una pregunta: el navegador envía la pregunta a /api/preguntar indicando el motor (prolog, llm o ambos). "
           "El servicio valida el texto (no vacío, máximo 500 caracteres), consulta los motores elegidos, mide el tiempo y "
           "devuelve las respuestas en JSON. Si un motor falla (por ejemplo, el LLM sin API key), la interfaz muestra el "
           "error sin afectar al otro motor.")

    # 5. Implementación
    doc.add_heading("5. Implementación", 1)
    doc.add_heading("5.1 Chatbot en Prolog", 2)
    viñetas(doc, [
        "**Normalización:** pasa el texto a minúsculas, quita tildes y signos (¿?¡!) y lo separa en palabras (normalizar/2).",
        "**Detección de especies:** busca los alias de cada especie, incluso de varias palabras (\"zorro de Darwin\", \"monito del monte\"), en singular o plural, y tolera un error de tipeo mediante distancia de edición 1 (\"guemul\" → huemul).",
        "**Intenciones:** con palabras clave reconoce si se pregunta por dieta, hábitat, conservación, amenazas, endemismo, clase, depredadores, datos curiosos o emblemas. Una pregunta puede tener varias intenciones (\"¿qué come y dónde vive…?\").",
        "**Listados con filtros:** si no se nombra una especie, combina condiciones (clase, zona, ecosistema, localidad, estado, dieta, alimento, endemismo) y lista las especies que cumplen todas, o las cuenta si se pregunta \"¿cuántas…?\".",
        "**Comparaciones:** con dos especies responde si comparten hábitat o cuáles son sus semejanzas y diferencias.",
        "**Respuestas:** se redactan en español con artículos y contracciones correctas (\"del puma\"). Si la pregunta no corresponde al dominio, lo dice explícitamente en lugar de inventar.",
    ])
    doc.add_heading("5.2 Chatbot con LLM en Python", 2)
    p(doc, "El LLM recibe en el mensaje de sistema la base de conocimiento completa (exportada desde Prolog) y reglas "
           "estrictas: responder solo con esa información, decir \"No tengo esa información\" cuando no esté, no salir del "
           "dominio, listar todas las especies que cumplan una condición y ninguna otra, y tolerar errores de ortografía. "
           "Se usa temperatura 0 para respuestas reproducibles y se envían los últimos turnos de la conversación para "
           "permitir preguntas de seguimiento (\"¿y dónde vive?\").")
    p(doc, f"El código usa la API compatible con OpenAI, por lo que funciona con Gemini, Groq, OpenAI u Ollama (local) "
           f"cambiando solo el archivo .env. En la evaluación de este informe se usó el modelo **{modelo}**."
           if llm_usado else
           "El código usa la API compatible con OpenAI, por lo que funciona con Gemini, Groq, OpenAI u Ollama (local) "
           "cambiando solo el archivo .env.")
    doc.add_heading("5.3 Interfaz web", 2)
    p(doc, "La interfaz (Flask + HTML/CSS/JavaScript sin frameworks) muestra un chat con tres modos: solo Prolog, solo LLM "
           "y \"Comparar ambos\", que muestra las dos respuestas lado a lado con su tiempo de respuesta. Incluye preguntas "
           "sugeridas, indicador del estado de cada motor y diseño adaptable a celulares.")
    doc.add_heading("5.4 Buenas prácticas aplicadas", 2)
    viñetas(doc, [
        "**Modularidad:** cada responsabilidad está en su propio módulo (motores, servicio, API, interfaz, evaluación).",
        "**Fuente única de verdad:** un cambio en conocimiento.pl se refleja de inmediato en ambos chatbots, sin reiniciar el servidor.",
        "**Robustez:** validación de entradas, tiempo máximo por consulta, manejo de errores por motor y respuestas explícitas fuera del dominio.",
        "**Seguridad:** la API key se lee desde .env (excluido de git) y la pregunta se pasa a Prolog por entrada estándar, no por la línea de comandos.",
        "**Pruebas automatizadas:** plunit para la lógica en Prolog y pytest para el backend (con un cliente LLM simulado).",
    ])

    # 6. Metodología
    doc.add_heading("6. Metodología de evaluación", 1)
    p(doc, "Se definieron **20 preguntas** que cubren distintos tipos de consulta: datos puntuales, preguntas de sí o no, "
           "listados con una y dos condiciones, inferencias que usan reglas, explicaciones, comparaciones, paráfrasis, un "
           "error de tipeo y una pregunta fuera del dominio. Cada pregunta tiene en evaluacion/preguntas.json una lista de "
           "elementos esperados y otra de elementos prohibidos (por ejemplo, especies que no deben aparecer en un listado).")
    tabla(doc, ["Resultado", "Criterio"], [
        ["Correcta (1 punto)", "Contiene todos los elementos esperados y ninguno prohibido"],
        ["Parcial (0,5 puntos)", "Contiene parte de lo esperado, o todo pero también algo prohibido"],
        ["Incorrecta (0 puntos)", "No contiene nada de lo esperado, o el motor no respondió"],
    ], [4.5, 12.1], colores=[[COLOR_ESTADO["correcta"], None], [COLOR_ESTADO["parcial"], None], [COLOR_ESTADO["incorrecta"], None]])
    p(doc, "Como las 20 preguntas se escribieron conociendo el sistema, se agregó un **set complementario de 10 preguntas** "
           "(evaluacion/preguntas_robustez.json) redactadas con otras palabras y no usadas para ajustar las reglas, para "
           "estimar cómo se comportaría cada chatbot frente a preguntas nuevas, como las que puede hacer el profesor en la "
           "interrogación. Todo el proceso se ejecuta con python -m evaluacion.evaluar.")

    # 7. Resultados
    doc.add_heading("7. Resultados", 1)
    p(doc, f"Evaluación ejecutada el {resultado['fecha']}.")
    motores = ["prolog", "llm"]
    nombres = {"prolog": "Prolog", "llm": f"LLM ({resultado['llm']['modelo']})"}

    def fila_resumen(etiqueta, clave):
        return [etiqueta] + [
            (str(rp[m][clave]) if m in rp else "Pendiente") for m in motores
        ]
    tabla(doc, ["Métrica (20 preguntas)", "Prolog", nombres["llm"]], [
        fila_resumen("Correctas", "correctas"),
        fila_resumen("Parciales", "parciales"),
        fila_resumen("Incorrectas", "incorrectas"),
        ["Puntaje"] + [f"{rp[m]['puntaje']:g} / {rp[m]['total']}" if m in rp else "Pendiente" for m in motores],
        ["Tiempo promedio de respuesta"] + [f"{rp[m]['tiempo_promedio_ms']} ms" if m in rp else "Pendiente" for m in motores],
        ["Puntaje set de robustez (10)"] + [f"{rr[m]['puntaje']:g} / {rr[m]['total']}" if m in rr else "Pendiente" for m in motores],
    ], [6.2, 5.2, 5.2])

    doc.add_heading("7.1 Respuestas a las 20 preguntas", 2)
    tabla(doc, ["#", "Pregunta (categoría)", "Respuesta Prolog", "Respuesta LLM"],
          [[f["id"], f"{f['pregunta']} ({f['categoria']})", celda_respuesta(f, "prolog"), celda_respuesta(f, "llm")] for f in filas],
          [0.8, 3.6, 6.1, 6.1], tam=8, colores=[color_fila(f, motores) for f in filas])

    doc.add_heading("7.2 Set complementario de robustez", 2)
    tabla(doc, ["#", "Pregunta (categoría)", "Respuesta Prolog", "Respuesta LLM"],
          [[f["id"], f"{f['pregunta']} ({f['categoria']})", celda_respuesta(f, "prolog"), celda_respuesta(f, "llm")] for f in robustez],
          [0.9, 3.5, 6.1, 6.1], tam=8, colores=[color_fila(f, motores) for f in robustez])

    # 8. Análisis
    doc.add_heading("8. Análisis de desempeño", 1)
    p(doc, frase_resumen("Prolog", rp["prolog"]))
    fallas_p = lista_ids(filas, "prolog", {"incorrecta", "parcial", "sin respuesta"})
    fallas_pr = lista_ids(robustez, "prolog", {"incorrecta", "parcial", "sin respuesta"})
    p(doc, "Prolog acierta casi siempre cuando la pregunta usa el vocabulario que sus reglas reconocen: datos puntuales, "
           "listados con varias condiciones, conteos, comparaciones e incluso un error de tipeo. Las respuestas son exactas "
           "y completas porque se calculan directamente sobre los hechos: si hay 6 especies en peligro, lista las 6. "
           f"Sus fallas en el set principal (pregunta(s) {', '.join(fallas_p) or 'ninguna'}) y en el set de robustez "
           f"(pregunta(s) {', '.join(fallas_pr) or 'ninguna'}) tienen la misma causa: la pregunta describe a la especie "
           "por un dato que solo está en un texto libre (\"felino más pequeño\", \"marsupial\", \"ataca gallinas\") o usa "
           "una expresión que no está en sus listas de palabras clave. En esos casos no entiende la pregunta y responde que "
           "no tiene la información o entrega una ficha general. "
           f"En el set de robustez su puntaje baja de {rp['prolog']['puntaje']:g}/20 a {rr['prolog']['puntaje']:g}/10, "
           "lo que muestra que su cobertura del lenguaje depende de las reglas escritas a mano.")
    if llm_usado:
        rl, rrl = rp["llm"], rr["llm"]
        fallas_l = lista_ids(filas, "llm", {"incorrecta", "parcial", "sin respuesta"})
        fallas_lr = lista_ids(robustez, "llm", {"incorrecta", "parcial", "sin respuesta"})
        solo_llm = [str(f["id"]) for f in filas + robustez
                    if f["llm"]["evaluacion"]["estado"] == "correcta" and f["prolog"]["evaluacion"]["estado"] != "correcta"]
        solo_prolog = [str(f["id"]) for f in filas + robustez
                       if f["prolog"]["evaluacion"]["estado"] == "correcta" and f["llm"]["evaluacion"]["estado"] != "correcta"]
        p(doc, frase_resumen(nombres["llm"], rl))
        texto = f"El LLM obtuvo {rl['puntaje']:g}/20 en el set principal y {rrl['puntaje']:g}/10 en el de robustez. "
        if solo_llm:
            texto += (f"Respondió bien preguntas que Prolog no entendió ({', '.join(solo_llm)}), porque interpreta el "
                      "significado de la pregunta y puede usar los datos curiosos y las amenazas escritas en texto libre. ")
        if fallas_l or fallas_lr:
            texto += (f"Tuvo respuestas incorrectas o parciales en: {', '.join(fallas_l + fallas_lr)}. Conviene revisar "
                      "en la tabla si se deben a especies omitidas o agregadas en listados, a conteos o a información "
                      "que no está en la base. ")
        else:
            texto += "No tuvo respuestas incorrectas ni parciales en ninguno de los dos sets. "
        texto += (f"Prolog acertó y el LLM no en: {', '.join(solo_prolog)}." if solo_prolog
                  else "No hubo preguntas en que Prolog acertara y el LLM no.")
        p(doc, texto)
        if rl["tiempo_promedio_ms"] and rp["prolog"]["tiempo_promedio_ms"]:
            factor = rl["tiempo_promedio_ms"] / max(rp["prolog"]["tiempo_promedio_ms"], 1)
            p(doc, f"En tiempo de respuesta, Prolog promedió {rp['prolog']['tiempo_promedio_ms']} ms y el LLM "
                   f"{rl['tiempo_promedio_ms']} ms, es decir, el LLM fue unas {factor:.0f} veces más lento, porque cada "
                   "consulta viaja por internet y el modelo procesa la base de conocimiento completa en cada pregunta.")
    else:
        p(doc, "**Resultados del LLM pendientes:** esta versión del informe se generó sin API key configurada. Para "
               "completar la columna del LLM y este análisis, configurar el archivo .env y ejecutar "
               "python -m evaluacion.evaluar; el informe se regenera automáticamente con los resultados reales.")

    # 9. Fortalezas y debilidades
    doc.add_heading("9. Fortalezas y debilidades de cada implementación", 1)
    tabla(doc, ["", "Prolog (lógica de primer orden)", "LLM con base de conocimiento"], [
        ["Fortalezas",
         "Respuestas exactas, verificables y siempre iguales para la misma pregunta.\n"
         "Listados y conteos completos: recorre todos los hechos sin olvidar ninguno.\n"
         "Razonamiento explicable: cada respuesta se puede rastrear hasta hechos y reglas.\n"
         "Muy rápido (decenas de milisegundos), gratuito y funciona sin internet.\n"
         "No inventa: si no sabe, lo dice.",
         "Entiende lenguaje natural variado: paráfrasis, sinónimos, plurales y errores de ortografía.\n"
         "Aprovecha la información en texto libre (datos curiosos, amenazas).\n"
         "Mantiene el contexto de la conversación (preguntas de seguimiento).\n"
         "Redacción más natural y flexible.\n"
         "Agregar una especie no requiere escribir reglas nuevas."],
        ["Debilidades",
         "Solo entiende las preguntas que coinciden con sus palabras clave; las paráfrasis fallan.\n"
         "No usa el contenido del texto libre para razonar.\n"
         "Cada nuevo tipo de pregunta requiere programar una regla.\n"
         "Las respuestas son de plantilla y a veces largas.",
         "Puede omitir o agregar elementos en listados largos y equivocarse al contar.\n"
         "Puede alucinar o mezclar conocimiento externo pese a las instrucciones.\n"
         "Más lento, depende de internet, de una API key y de cuotas de uso.\n"
         "No es totalmente reproducible ni explicable paso a paso.\n"
         "El costo crece con el tamaño de la base, porque se envía completa en cada consulta."],
    ], [2.6, 7.0, 7.0])

    # 10. Conclusiones
    doc.add_heading("10. Conclusiones", 1)
    viñetas(doc, [
        "Ambas versiones responden con el mismo conocimiento gracias a que la base en lógica de primer orden es la única fuente de verdad; esto permitió compararlas de forma justa.",
        "Prolog es la opción más **confiable**: cuando entiende la pregunta, la respuesta es correcta, completa y explicable. Su límite está en la comprensión del lenguaje, no en el razonamiento.",
        "El LLM es la opción más **flexible**: entiende preguntas formuladas libremente, pero no garantiza exactitud en listados y conteos, es más lento y depende de un servicio externo.",
        "Los resultados muestran que los dos enfoques son complementarios: la lógica aporta precisión y trazabilidad, y el modelo de lenguaje aporta comprensión del lenguaje natural.",
    ])

    # 11. Propuestas
    doc.add_heading("11. Propuestas para mejorar el desempeño", 1)
    viñetas(doc, [
        "**Sistema híbrido (LLM + Prolog):** usar el LLM solo para traducir la pregunta a una consulta Prolog (por ejemplo, \"¿qué aves del altiplano están amenazadas?\" → findall con clase, ecosistema y amenazada) y dejar que Prolog calcule la respuesta. Combina la comprensión del LLM con la exactitud de la lógica.",
        "**Respaldo automático:** si Prolog no reconoce la pregunta, derivarla al LLM, indicando al usuario qué motor respondió.",
        "**Más conocimiento estructurado:** convertir los datos curiosos en hechos (tamaño, peso, si vuela, si es marsupial, actividad diurna o nocturna) para que Prolog pueda razonar sobre ellos.",
        "**Mejor procesamiento del lenguaje en Prolog:** gramáticas DCG para frases completas, diccionario de sinónimos (felino → puma, güiña; ciervo → huemul, pudú) y lematización.",
        "**Recuperación selectiva (RAG):** con una base más grande, enviar al LLM solo las especies relevantes a la pregunta para reducir costo, tiempo y errores en listados.",
        "**Verificación de respuestas del LLM:** comprobar con Prolog las especies que menciona el LLM y advertir cuando nombre una que no cumple la condición.",
        "**Evaluación continua:** ampliar el set de preguntas con las que hagan usuarios reales e incorporar evaluación humana además de la automática.",
    ])

    # Anexo
    doc.add_heading("Anexo: cómo ejecutar el sistema", 1)
    codigo(doc, """
# Requisitos: Python 3.10+ y SWI-Prolog en el PATH
pip install -r requirements.txt
cp .env.example .env          # y pegar la API key del LLM
python -m backend.app         # abrir http://localhost:5000

# Chatbot Prolog en consola
cd prolog && swipl main.pl

# Pruebas y evaluación
cd prolog && swipl -g run_tests -t halt tests/test_chatbot.pl && cd ..
python -m pytest -q
python -m evaluacion.evaluar""")

    doc.save(SALIDA)
    return SALIDA


if __name__ == "__main__":
    print(f"Informe generado: {generar()}")
