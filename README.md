# Proyecto 2 — Chatbot de fauna nativa de Chile

Fundamentos de Inteligencia Artificial · Ingeniería Civil Informática · UNAB

Chatbot que responde preguntas sobre la fauna nativa de Chile, implementado de dos formas:

1. **Lógica de primer orden en Prolog** (`prolog/`)
2. **LLM con Python** (`backend/motor_llm.py`), usando el mismo conocimiento

Incluye una **interfaz web** para usar cada versión o compararlas lado a lado, además del **informe de desempeño** con 20 preguntas (`informe/`).

## Estructura

```
prolog/
  conocimiento.pl      Base de conocimiento: 23 especies, hechos y reglas (fuente única de verdad)
  chatbot.pl           Comprensión de la pregunta y generación de respuestas
  main.pl              Punto de entrada por consola
  tests/               Pruebas unitarias (plunit)
backend/
  motor_prolog.py      Puente Python → SWI-Prolog
  conocimiento.py      Exporta la base de Prolog a texto para el LLM
  motor_llm.py         Chatbot LLM (Gemini, Groq, OpenAI u Ollama)
  servicio.py          Validación, tiempos y orquestación de motores
  app.py               Servidor Flask (API + interfaz)
frontend/              Interfaz web (HTML, CSS, JS)
evaluacion/            20 preguntas + 10 de robustez, script de evaluación y resultados
informe/               Generador e informe Word de la entrega
tests/                 Pruebas del backend (pytest)
```

## Instalación

Requisitos: **Python 3.10+** y **SWI-Prolog** (https://www.swi-prolog.org/download/stable) en el PATH.

```bash
pip install -r requirements.txt
cp .env.example .env      # en Windows: copy .env.example .env
```

Edita `.env` y pega tu API key. Opciones gratuitas:

| Proveedor | Dónde obtener la key | `.env` |
|---|---|---|
| Gemini | https://aistudio.google.com/apikey | `LLM_PROVEEDOR=gemini` |
| Groq | https://console.groq.com/keys | `LLM_PROVEEDOR=groq` |
| Ollama (local, sin key) | https://ollama.com | `LLM_PROVEEDOR=ollama` |

Si el modelo por defecto no está disponible en tu cuenta, cámbialo con `LLM_MODELO=...`.

## Uso

```bash
python -m backend.app          # abrir http://localhost:5000
```

Chatbot Prolog en consola:

```bash
cd prolog
swipl main.pl                       # chat interactivo
swipl main.pl "¿Qué come el pudú?"   # una pregunta
```

O cargándolo en el intérprete: `swipl chatbot.pl` y luego `?- chat.` o `?- responder("¿Dónde vive el huillín?", R).`

## Pruebas y evaluación

```bash
cd prolog && swipl -g run_tests -t halt tests/test_chatbot.pl && cd ..
python -m pytest -q
python -m evaluacion.evaluar        # corre las 20 preguntas en ambos motores y regenera el informe
```

## Modificar el conocimiento (para la interrogación)

Todo el conocimiento está en `prolog/conocimiento.pl`. Al guardar un cambio, **ambos chatbots lo usan de inmediato** (no hay que reiniciar el servidor). Ejemplo: agregar una especie

```prolog
especie(loica, 'loica', 'Leistes loyca').
clase(loica, ave).
dieta(loica, omnivoro).
come(loica, insectos). come(loica, semillas).
ecosistema(loica, matorral_central).
zona(loica, centro). zona(loica, sur).
conservacion(loica, lc).
alias(loica, "loica").
femenino(loica).                 % para que responda "la loica"
```

Cada especie necesita al menos `especie/3`, `clase/2`, `dieta/2`, `ecosistema/2`, `zona/2`, `conservacion/2` y un `alias/2` (en minúsculas y sin tildes). Si el nombre es femenino (la vicuña, la loica), agrega `femenino/1`.
