:- encoding(utf8).
/*  Pruebas unitarias del chatbot Prolog (plunit).
    Ejecutar desde la carpeta prolog/:  swipl -g run_tests -t halt tests/test_chatbot.pl
*/
:- use_module(library(plunit)).
:- ensure_loaded('../chatbot').

contiene(Resp, Sub) :- sub_string(Resp, _, _, _, Sub).

:- begin_tests(normalizacion).
test(tildes_y_signos) :- normalizar("¿Qué come el PUDÚ?", T), T == [que, come, el, pudu].
test(enie) :- normalizar("ñandú", [nandu]).
:- end_tests(normalizacion).

:- begin_tests(deteccion).
test(alias_multipalabra) :- normalizar("háblame del zorro de darwin", T), especies_mencionadas(T, [zorro_darwin]).
test(dos_especies_en_orden) :- normalizar("el puma y el guanaco", T), especies_mencionadas(T, [puma, guanaco]).
test(error_de_tipeo) :- normalizar("que come el guemul", T), especies_mencionadas(T, [huemul]).
test(plurales) :- normalizar("qué comen los pudúes y los huemules", T), especies_mencionadas(T, [pudu, huemul]).
test(sin_falso_positivo) :- normalizar("que bonito dia", T), especies_mencionadas(T, []).
:- end_tests(deteccion).

:- begin_tests(reglas).
test(amenazada) :- amenazada(condor).
test(no_amenazada, [fail]) :- amenazada(puma).
test(en_peligro, all(X == [huemul, zorro_darwin, chinchilla, huillin, chungungo, ranita_darwin])) :- en_peligro(X).
test(depredador) :- depredador_de(puma, pudu).
test(comparten) :- comparten_habitat(puma, guanaco), !.
:- end_tests(reglas).

:- begin_tests(respuestas).
test(dieta) :- responder("¿Qué come el pudú?", R), contiene(R, "herbívora").
test(cientifico) :- responder("nombre científico del huemul", R), contiene(R, "Hippocamelus bisulcus").
test(listado) :- responder("¿Qué aves viven en el altiplano?", R), contiene(R, "flamenco"), contiene(R, "ñandú").
test(conteo) :- responder("¿Cuántas especies en peligro hay?", R), contiene(R, "Hay 6").
test(amenazas) :- responder("¿Por qué el huemul está en peligro?", R), contiene(R, "caza furtiva").
test(clase_negativa) :- responder("¿La vicuña es un ave?", R), contiene(R, "No, la vicuña no es un ave").
test(fuera_de_dominio) :- responder("¿Cuál es la capital de Francia?", R), contiene(R, "No tengo información").
test(vacio) :- responder("", R), contiene(R, "Escribe una pregunta").
:- end_tests(respuestas).
