:- encoding(utf8).
/*  ==========================================================================
    Base de conocimiento: Fauna nativa de Chile
    Proyecto 2 - Fundamentos de Inteligencia Artificial (UNAB)

    Modelo en lógica de primer orden:
      Dominio: especies de fauna nativa de Chile y sus atributos.
      Constantes: identificadores de especies (huemul, pudu, ...), clases,
                  zonas, ecosistemas, estados de conservación y alimentos.
      Predicados base (hechos):
        especie(E, NombreComun, NombreCientifico)
        clase(E, C)              C ∈ {mamifero, ave, anfibio}
        dieta(E, D)              D ∈ {herbivoro, carnivoro, omnivoro, insectivoro, carronero}
        come(E, A)               A es un alimento o una especie de la base
        ecosistema(E, H)
        zona(E, Z)               Z ∈ {norte, centro, sur, austral}
        conservacion(E, S)       S ∈ {lc, nt, vu, en, cr}  (Lista Roja UICN)
        endemica_chile(E)
        localidad(E, L)
        amenaza(E, Texto)
        emblema_nacional(E)
        dato_curioso(E, Texto)
      Predicados derivados (reglas): amenazada/1, en_peligro/1,
        depredador_de/2, comparten_habitat/2, comparten_zona/2, ...

    Fuente principal de estados de conservación: Lista Roja de la UICN.
    ========================================================================== */

:- discontiguous especie/3, clase/2, dieta/2, come/2, ecosistema/2, zona/2,
                 conservacion/2, endemica_chile/1, localidad/2, amenaza/2,
                 dato_curioso/2, emblema_nacional/1.
:- dynamic especie/3, clase/2, dieta/2, come/2, ecosistema/2, zona/2,
           conservacion/2, endemica_chile/1, localidad/2, amenaza/2,
           emblema_nacional/1, dato_curioso/2, alias/2, femenino/1.

/* ----------------------------- MAMÍFEROS -------------------------------- */

especie(huemul, 'huemul', 'Hippocamelus bisulcus').
clase(huemul, mamifero).
dieta(huemul, herbivoro).
come(huemul, hojas). come(huemul, brotes). come(huemul, pasto).
ecosistema(huemul, bosque_templado). ecosistema(huemul, cordillera_andina).
zona(huemul, sur). zona(huemul, austral).
conservacion(huemul, en).
localidad(huemul, torres_del_paine).
amenaza(huemul, 'pérdida y fragmentación de su hábitat').
amenaza(huemul, 'caza furtiva').
amenaza(huemul, 'ataques de perros').
amenaza(huemul, 'enfermedades transmitidas por el ganado').
emblema_nacional(huemul).
dato_curioso(huemul, 'aparece en el escudo nacional de Chile junto al cóndor').

especie(pudu, 'pudú', 'Pudu puda').
clase(pudu, mamifero).
dieta(pudu, herbivoro).
come(pudu, hojas). come(pudu, brotes). come(pudu, frutos).
ecosistema(pudu, bosque_templado).
zona(pudu, centro). zona(pudu, sur). zona(pudu, austral).
conservacion(pudu, nt).
localidad(pudu, chiloe).
amenaza(pudu, 'pérdida de bosque nativo').
amenaza(pudu, 'ataques de perros').
amenaza(pudu, 'atropellos en caminos').
dato_curioso(pudu, 'es uno de los ciervos más pequeños del mundo: mide unos 40 cm de alto').

especie(puma, 'puma', 'Puma concolor').
clase(puma, mamifero).
dieta(puma, carnivoro).
come(puma, guanaco). come(puma, huemul). come(puma, pudu). come(puma, vicuna).
come(puma, roedores).
ecosistema(puma, cordillera_andina). ecosistema(puma, bosque_templado).
ecosistema(puma, estepa_patagonica). ecosistema(puma, matorral_central).
zona(puma, norte). zona(puma, centro). zona(puma, sur). zona(puma, austral).
conservacion(puma, lc).
localidad(puma, torres_del_paine).
amenaza(puma, 'conflicto con ganaderos (caza en represalia)').
dato_curioso(puma, 'es el mayor felino de Chile y el principal depredador del guanaco').

especie(culpeo, 'zorro culpeo', 'Lycalopex culpaeus').
clase(culpeo, mamifero).
dieta(culpeo, omnivoro).
come(culpeo, roedores). come(culpeo, degu). come(culpeo, cururo).
come(culpeo, aves). come(culpeo, frutos).
ecosistema(culpeo, cordillera_andina). ecosistema(culpeo, matorral_central).
ecosistema(culpeo, estepa_patagonica).
zona(culpeo, norte). zona(culpeo, centro). zona(culpeo, sur). zona(culpeo, austral).
conservacion(culpeo, lc).
localidad(culpeo, torres_del_paine).
dato_curioso(culpeo, 'es el zorro más grande de Chile; también se le llama zorro colorado').

especie(zorro_darwin, 'zorro de Darwin', 'Lycalopex fulvipes').
clase(zorro_darwin, mamifero).
dieta(zorro_darwin, omnivoro).
come(zorro_darwin, insectos). come(zorro_darwin, roedores). come(zorro_darwin, frutos).
ecosistema(zorro_darwin, bosque_templado).
zona(zorro_darwin, sur).
conservacion(zorro_darwin, en).
endemica_chile(zorro_darwin).
localidad(zorro_darwin, chiloe). localidad(zorro_darwin, nahuelbuta).
amenaza(zorro_darwin, 'ataques y enfermedades de perros domésticos').
amenaza(zorro_darwin, 'pérdida de bosque nativo').
dato_curioso(zorro_darwin, 'fue descrito por Charles Darwin en Chiloé en 1834').

especie(guanaco, 'guanaco', 'Lama guanicoe').
clase(guanaco, mamifero).
dieta(guanaco, herbivoro).
come(guanaco, pasto). come(guanaco, arbustos).
ecosistema(guanaco, cordillera_andina). ecosistema(guanaco, estepa_patagonica).
ecosistema(guanaco, desierto).
zona(guanaco, norte). zona(guanaco, centro). zona(guanaco, austral).
conservacion(guanaco, lc).
localidad(guanaco, torres_del_paine).
dato_curioso(guanaco, 'es el camélido silvestre más grande de Sudamérica').

especie(vicuna, 'vicuña', 'Vicugna vicugna').
clase(vicuna, mamifero).
dieta(vicuna, herbivoro).
come(vicuna, pasto).
ecosistema(vicuna, altiplano).
zona(vicuna, norte).
conservacion(vicuna, lc).
localidad(vicuna, lauca).
amenaza(vicuna, 'caza furtiva por su fibra (histórica)').
dato_curioso(vicuna, 'produce una de las fibras animales más finas del mundo').

especie(chinchilla, 'chinchilla', 'Chinchilla lanigera').
clase(chinchilla, mamifero).
dieta(chinchilla, herbivoro).
come(chinchilla, hierbas). come(chinchilla, semillas).
ecosistema(chinchilla, matorral_central).
zona(chinchilla, norte).
conservacion(chinchilla, en).
amenaza(chinchilla, 'caza histórica por su piel').
amenaza(chinchilla, 'pérdida de hábitat por minería y pastoreo').
dato_curioso(chinchilla, 'su pelaje es uno de los más densos entre los mamíferos terrestres').

especie(degu, 'degú', 'Octodon degus').
clase(degu, mamifero).
dieta(degu, herbivoro).
come(degu, pasto). come(degu, hojas). come(degu, semillas).
ecosistema(degu, matorral_central).
zona(degu, norte). zona(degu, centro).
conservacion(degu, lc).
endemica_chile(degu).
dato_curioso(degu, 'es un roedor diurno y muy social que vive en colonias').

especie(cururo, 'cururo', 'Spalacopus cyanus').
clase(cururo, mamifero).
dieta(cururo, herbivoro).
come(cururo, raices). come(cururo, tuberculos).
ecosistema(cururo, matorral_central).
zona(cururo, centro).
conservacion(cururo, lc).
endemica_chile(cururo).
dato_curioso(cururo, 'vive en galerías subterráneas que cava en colonias').

especie(monito, 'monito del monte', 'Dromiciops gliroides').
clase(monito, mamifero).
dieta(monito, omnivoro).
come(monito, insectos). come(monito, frutos).
ecosistema(monito, bosque_templado).
zona(monito, sur).
conservacion(monito, nt).
localidad(monito, chiloe).
amenaza(monito, 'pérdida y fragmentación del bosque nativo').
dato_curioso(monito, 'es un marsupial, el único sobreviviente del orden Microbiotheria, e hiberna en invierno').

especie(guina, 'güiña', 'Leopardus guigna').
clase(guina, mamifero).
dieta(guina, carnivoro).
come(guina, roedores). come(guina, aves). come(guina, lagartijas).
ecosistema(guina, bosque_templado). ecosistema(guina, matorral_central).
zona(guina, centro). zona(guina, sur). zona(guina, austral).
conservacion(guina, vu).
localidad(guina, chiloe). localidad(guina, nahuelbuta).
amenaza(guina, 'pérdida y fragmentación del bosque').
amenaza(guina, 'persecución por ataques a aves de corral').
dato_curioso(guina, 'es el felino más pequeño de América').

especie(huillin, 'huillín', 'Lontra provocax').
clase(huillin, mamifero).
dieta(huillin, carnivoro).
come(huillin, peces). come(huillin, crustaceos).
ecosistema(huillin, rios_y_lagos).
zona(huillin, sur). zona(huillin, austral).
conservacion(huillin, en).
amenaza(huillin, 'pérdida del bosque ribereño').
amenaza(huillin, 'contaminación de ríos').
amenaza(huillin, 'competencia con el visón americano (especie invasora)').
dato_curioso(huillin, 'es la nutria de agua dulce de Chile').

especie(chungungo, 'chungungo', 'Lontra felina').
clase(chungungo, mamifero).
dieta(chungungo, carnivoro).
come(chungungo, peces). come(chungungo, crustaceos). come(chungungo, moluscos).
ecosistema(chungungo, costa_marina).
zona(chungungo, norte). zona(chungungo, centro). zona(chungungo, sur). zona(chungungo, austral).
conservacion(chungungo, en).
amenaza(chungungo, 'caza histórica por su piel').
amenaza(chungungo, 'contaminación y alteración de la costa').
dato_curioso(chungungo, 'es la nutria marina más pequeña del mundo').

/* -------------------------------- AVES ---------------------------------- */

especie(condor, 'cóndor andino', 'Vultur gryphus').
clase(condor, ave).
dieta(condor, carronero).
come(condor, carrona).
ecosistema(condor, cordillera_andina). ecosistema(condor, costa_marina).
zona(condor, norte). zona(condor, centro). zona(condor, sur). zona(condor, austral).
conservacion(condor, vu).
localidad(condor, torres_del_paine).
amenaza(condor, 'envenenamiento con cebos tóxicos').
amenaza(condor, 'caza ilegal').
amenaza(condor, 'choques con tendidos eléctricos').
emblema_nacional(condor).
dato_curioso(condor, 'es una de las aves voladoras más grandes del mundo, con unos 3 m de envergadura').

especie(pinguino, 'pingüino de Humboldt', 'Spheniscus humboldti').
clase(pinguino, ave).
dieta(pinguino, carnivoro).
come(pinguino, peces).
ecosistema(pinguino, costa_marina).
zona(pinguino, norte). zona(pinguino, centro). zona(pinguino, sur).
conservacion(pinguino, vu).
localidad(pinguino, chiloe).
amenaza(pinguino, 'captura incidental en redes de pesca').
amenaza(pinguino, 'sobrepesca de sus presas').
amenaza(pinguino, 'perturbación de sus colonias').
dato_curioso(pinguino, 'su nombre viene de la corriente de Humboldt').

especie(flamenco, 'flamenco chileno', 'Phoenicopterus chilensis').
clase(flamenco, ave).
dieta(flamenco, omnivoro).
come(flamenco, crustaceos). come(flamenco, algas).
ecosistema(flamenco, humedales). ecosistema(flamenco, altiplano).
zona(flamenco, norte). zona(flamenco, centro). zona(flamenco, austral).
conservacion(flamenco, nt).
localidad(flamenco, lauca).
amenaza(flamenco, 'alteración de humedales y salares').
dato_curioso(flamenco, 'se alimenta filtrando el agua con su pico curvo').

especie(carpintero, 'carpintero negro', 'Campephilus magellanicus').
clase(carpintero, ave).
dieta(carpintero, insectivoro).
come(carpintero, insectos).
ecosistema(carpintero, bosque_templado).
zona(carpintero, sur). zona(carpintero, austral).
conservacion(carpintero, lc).
amenaza(carpintero, 'tala de bosques antiguos').
dato_curioso(carpintero, 'es el carpintero más grande de Sudamérica').

especie(choroy, 'choroy', 'Enicognathus leptorhynchus').
clase(choroy, ave).
dieta(choroy, herbivoro).
come(choroy, semillas). come(choroy, pinones).
ecosistema(choroy, bosque_templado).
zona(choroy, centro). zona(choroy, sur).
conservacion(choroy, lc).
endemica_chile(choroy).
dato_curioso(choroy, 'es un loro que usa su pico largo para extraer piñones de araucaria').

especie(nandu, 'ñandú', 'Rhea pennata').
clase(nandu, ave).
dieta(nandu, omnivoro).
come(nandu, hojas). come(nandu, semillas). come(nandu, insectos).
ecosistema(nandu, altiplano). ecosistema(nandu, estepa_patagonica).
zona(nandu, norte). zona(nandu, austral).
conservacion(nandu, lc).
localidad(nandu, lauca). localidad(nandu, torres_del_paine).
dato_curioso(nandu, 'no vuela, y es el macho quien incuba los huevos').

especie(chucao, 'chucao', 'Scelorchilus rubecula').
clase(chucao, ave).
dieta(chucao, insectivoro).
come(chucao, insectos).
ecosistema(chucao, bosque_templado).
zona(chucao, sur).
conservacion(chucao, lc).
localidad(chucao, chiloe).
dato_curioso(chucao, 'su canto es muy fuerte y en la tradición popular se considera un augurio').

/* ------------------------------ ANFIBIOS -------------------------------- */

especie(ranita_darwin, 'ranita de Darwin', 'Rhinoderma darwinii').
clase(ranita_darwin, anfibio).
dieta(ranita_darwin, insectivoro).
come(ranita_darwin, insectos).
ecosistema(ranita_darwin, bosque_templado).
zona(ranita_darwin, sur).
conservacion(ranita_darwin, en).
localidad(ranita_darwin, chiloe).
amenaza(ranita_darwin, 'quitridiomicosis (enfermedad causada por un hongo)').
amenaza(ranita_darwin, 'pérdida del bosque nativo').
dato_curioso(ranita_darwin, 'el macho incuba los renacuajos dentro de su saco vocal').

especie(rana_grande, 'rana grande chilena', 'Calyptocephalella gayi').
clase(rana_grande, anfibio).
dieta(rana_grande, carnivoro).
come(rana_grande, insectos). come(rana_grande, peces).
ecosistema(rana_grande, rios_y_lagos). ecosistema(rana_grande, humedales).
zona(rana_grande, centro). zona(rana_grande, sur).
conservacion(rana_grande, vu).
endemica_chile(rana_grande).
amenaza(rana_grande, 'captura para consumo humano').
amenaza(rana_grande, 'pérdida de humedales').
dato_curioso(rana_grande, 'es la rana más grande de Chile y se le considera un fósil viviente').

/* ---------------------- ALIAS (cómo la gente las nombra) ---------------- */
/* Se escriben en minúsculas y sin tildes: el chatbot normaliza el texto.   */

alias(huemul, "huemul").
alias(pudu, "pudu").
alias(puma, "puma"). alias(puma, "leon de montana").
alias(culpeo, "zorro culpeo"). alias(culpeo, "culpeo"). alias(culpeo, "zorro colorado").
alias(zorro_darwin, "zorro de darwin"). alias(zorro_darwin, "zorro chilote").
alias(guanaco, "guanaco").
alias(vicuna, "vicuna").
alias(chinchilla, "chinchilla").
alias(degu, "degu").
alias(cururo, "cururo"). alias(cururo, "coruro").
alias(monito, "monito del monte"). alias(monito, "monito").
alias(guina, "guina"). alias(guina, "kodkod").
alias(huillin, "huillin"). alias(huillin, "nutria de rio").
alias(chungungo, "chungungo"). alias(chungungo, "nutria marina"). alias(chungungo, "gato de mar").
alias(condor, "condor andino"). alias(condor, "condor").
alias(pinguino, "pinguino de humboldt"). alias(pinguino, "pinguino").
alias(flamenco, "flamenco chileno"). alias(flamenco, "flamenco").
alias(carpintero, "carpintero negro"). alias(carpintero, "carpintero").
alias(choroy, "choroy").
alias(nandu, "nandu"). alias(nandu, "suri"). alias(nandu, "choique").
alias(chucao, "chucao").
alias(ranita_darwin, "ranita de darwin"). alias(ranita_darwin, "rana de darwin").
alias(rana_grande, "rana grande chilena"). alias(rana_grande, "rana chilena"). alias(rana_grande, "rana grande").

/* Nombres comunes femeninos (para usar "la" en vez de "el" en las respuestas) */
femenino(vicuna). femenino(chinchilla). femenino(guina).
femenino(ranita_darwin). femenino(rana_grande).

/* ------------------------- ETIQUETAS PARA RESPUESTAS -------------------- */

nombre_estado(lc, 'preocupación menor (LC)').
nombre_estado(nt, 'casi amenazada (NT)').
nombre_estado(vu, 'vulnerable (VU)').
nombre_estado(en, 'en peligro (EN)').
nombre_estado(cr, 'en peligro crítico (CR)').

nombre_clase(mamifero, 'mamífero', 'mamíferos').
nombre_clase(ave, 'ave', 'aves').
nombre_clase(anfibio, 'anfibio', 'anfibios').

nombre_dieta(herbivoro, 'herbívoro').
nombre_dieta(carnivoro, 'carnívoro').
nombre_dieta(omnivoro, 'omnívoro').
nombre_dieta(insectivoro, 'insectívoro').
nombre_dieta(carronero, 'carroñero').

nombre_zona(norte, 'zona norte').
nombre_zona(centro, 'zona centro').
nombre_zona(sur, 'zona sur').
nombre_zona(austral, 'zona austral').

nombre_ecosistema(altiplano, 'el altiplano').
nombre_ecosistema(cordillera_andina, 'la cordillera de los Andes').
nombre_ecosistema(desierto, 'el desierto').
nombre_ecosistema(matorral_central, 'el matorral de la zona central').
nombre_ecosistema(bosque_templado, 'el bosque templado').
nombre_ecosistema(estepa_patagonica, 'la estepa patagónica').
nombre_ecosistema(costa_marina, 'la costa marina').
nombre_ecosistema(rios_y_lagos, 'ríos y lagos').
nombre_ecosistema(humedales, 'humedales y salares').

nombre_localidad(chiloe, 'Chiloé').
nombre_localidad(nahuelbuta, 'la cordillera de Nahuelbuta').
nombre_localidad(torres_del_paine, 'Torres del Paine').
nombre_localidad(lauca, 'el Parque Nacional Lauca').

nombre_alimento(hojas, 'hojas').
nombre_alimento(brotes, 'brotes').
nombre_alimento(pasto, 'pasto').
nombre_alimento(frutos, 'frutos').
nombre_alimento(semillas, 'semillas').
nombre_alimento(hierbas, 'hierbas').
nombre_alimento(arbustos, 'arbustos').
nombre_alimento(raices, 'raíces').
nombre_alimento(tuberculos, 'tubérculos').
nombre_alimento(pinones, 'piñones').
nombre_alimento(insectos, 'insectos').
nombre_alimento(roedores, 'roedores').
nombre_alimento(aves, 'aves pequeñas').
nombre_alimento(lagartijas, 'lagartijas').
nombre_alimento(peces, 'peces').
nombre_alimento(crustaceos, 'crustáceos').
nombre_alimento(moluscos, 'moluscos').
nombre_alimento(algas, 'algas').
nombre_alimento(carrona, 'carroña (animales muertos)').

/* ------------------------------- REGLAS --------------------------------- */

% ∀x (conservacion(x, s) ∧ s ∈ {vu, en, cr} → amenazada(x))
amenazada(X) :- conservacion(X, S), memberchk(S, [vu, en, cr]).

% ∀x (conservacion(x, s) ∧ s ∈ {en, cr} → en_peligro(x))
en_peligro(X) :- conservacion(X, S), memberchk(S, [en, cr]).

% ∀p ∀x (come(p, x) ∧ especie(x) → depredador_de(p, x))
depredador_de(P, X) :- come(P, X), especie(X, _, _).

% ∀x ∀y ∃h (ecosistema(x, h) ∧ ecosistema(y, h) ∧ x ≠ y → comparten_habitat(x, y))
comparten_habitat(X, Y) :- ecosistema(X, H), ecosistema(Y, H), X \= Y.

habitat_comun(X, Y, H) :- ecosistema(X, H), ecosistema(Y, H).

comparten_zona(X, Y) :- zona(X, Z), zona(Y, Z), X \= Y.

% Una especie es carnívora en sentido amplio si come otros animales.
consume_animales(X) :- come(X, A),
    ( especie(A, _, _) ; memberchk(A, [roedores, aves, lagartijas, peces,
                                       crustaceos, moluscos, insectos, carrona]) ).

especie_id(X) :- especie(X, _, _).
