// Interfaz del chatbot: envía la pregunta a la API y muestra las respuestas.
const chat = document.getElementById("chat");
const formulario = document.getElementById("formulario");
const campo = document.getElementById("pregunta");
const botonEnviar = document.getElementById("enviar");
const estado = document.getElementById("estado");

const SUGERENCIAS = [
  "¿Qué come el pudú?",
  "¿Dónde vive el huillín?",
  "¿Qué animales están en peligro?",
  "¿Qué aves viven en el altiplano?",
  "¿Por qué el huemul está en peligro?",
  "¿El puma y el guanaco comparten hábitat?",
];

let motor = "prolog";
let historialLLM = []; // contexto de conversación solo para el LLM

function agregarMensaje(clase, texto) {
  const div = document.createElement("div");
  div.className = `mensaje ${clase}`;
  div.textContent = texto;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

function tarjetaRespuesta(nombre, resultado) {
  const div = document.createElement("div");
  div.className = "mensaje bot" + (resultado.error ? " error" : "");
  const etiqueta = document.createElement("span");
  etiqueta.className = `etiqueta ${nombre}`;
  etiqueta.textContent = nombre === "prolog" ? "Prolog (lógica de primer orden)" : "LLM";
  const cuerpo = document.createElement("div");
  cuerpo.textContent = resultado.error ? `⚠ ${resultado.error}` : resultado.texto;
  const tiempo = document.createElement("span");
  tiempo.className = "tiempo";
  tiempo.textContent = `${resultado.ms} ms`;
  div.append(etiqueta, cuerpo, tiempo);
  return div;
}

function mostrarRespuestas(respuestas) {
  const nombres = ["prolog", "llm"].filter((n) => n in respuestas);
  if (nombres.length === 1) {
    chat.appendChild(tarjetaRespuesta(nombres[0], respuestas[nombres[0]]));
  } else {
    const fila = document.createElement("div");
    fila.className = "fila-bots";
    nombres.forEach((n) => fila.appendChild(tarjetaRespuesta(n, respuestas[n])));
    chat.appendChild(fila);
  }
  chat.scrollTop = chat.scrollHeight;
}

async function preguntar(texto) {
  agregarMensaje("usuario", texto);
  const espera = agregarMensaje("bot cargando", "Pensando…");
  botonEnviar.disabled = true;
  try {
    const r = await fetch("/api/preguntar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pregunta: texto, motor, historial: historialLLM }),
    });
    const datos = await r.json();
    espera.remove();
    if (!r.ok) {
      agregarMensaje("bot error", `⚠ ${datos.error || "Error del servidor"}`);
      return;
    }
    mostrarRespuestas(datos.respuestas);
    const llm = datos.respuestas.llm;
    if (llm && llm.texto) {
      historialLLM.push({ role: "user", content: texto }, { role: "assistant", content: llm.texto });
      historialLLM = historialLLM.slice(-6);
    }
  } catch (e) {
    espera.remove();
    agregarMensaje("bot error", "⚠ No se pudo conectar con el servidor. ¿Está corriendo python -m backend.app?");
  } finally {
    botonEnviar.disabled = false;
    campo.focus();
  }
}

formulario.addEventListener("submit", (e) => {
  e.preventDefault();
  const texto = campo.value.trim();
  if (!texto) return;
  campo.value = "";
  preguntar(texto);
});

document.querySelectorAll(".modo").forEach((boton) => {
  boton.addEventListener("click", () => {
    document.querySelectorAll(".modo").forEach((b) => {
      b.classList.remove("activo");
      b.setAttribute("aria-checked", "false");
    });
    boton.classList.add("activo");
    boton.setAttribute("aria-checked", "true");
    motor = boton.dataset.motor;
  });
});

document.getElementById("limpiar").addEventListener("click", () => {
  chat.innerHTML = "";
  historialLLM = [];
  saludo();
});

const contenedorSugerencias = document.getElementById("sugerencias");
SUGERENCIAS.forEach((s) => {
  const chip = document.createElement("button");
  chip.className = "chip";
  chip.type = "button";
  chip.textContent = s;
  chip.addEventListener("click", () => preguntar(s));
  contenedorSugerencias.appendChild(chip);
});

function saludo() {
  agregarMensaje("bot", "¡Hola! Pregúntame sobre la fauna nativa de Chile: qué comen, dónde viven, su estado de conservación y más. Elige arriba si quieres que responda Prolog, el LLM o ambos.");
}

async function cargarEstado() {
  try {
    const d = await (await fetch("/api/estado")).json();
    const p = d.prolog ? "Prolog ✓" : "Prolog ✗";
    const l = d.llm ? `LLM ✓ (${d.modelo_llm})` : "LLM sin configurar";
    estado.textContent = `${p} · ${l} · ${d.especies} especies`;
  } catch {
    estado.textContent = "Servidor no disponible";
  }
}

saludo();
cargarEstado();
