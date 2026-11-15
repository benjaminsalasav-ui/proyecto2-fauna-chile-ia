:- encoding(utf8).
/*  ==========================================================================
    Chatbot en Prolog: Fauna nativa de Chile
    Proyecto 2 - Fundamentos de Inteligencia Artificial (UNAB)

    Flujo:  texto  ->  normalizar/2 (minúsculas, sin tildes, tokens)
                   ->  especies_mencionadas/2 + intenciones / filtros
                   ->  consultas a la base de conocimiento (conocimiento.pl)
                   ->  respuesta en español

    Uso interactivo:   ?- chat.
    Uso directo:       ?- responder("¿Qué come el pudú?", R).
    ========================================================================== */

:- ensure_loaded(conocimiento).
:- use_module(library(lists)).
:- use_module(library(apply)).
:- use_module(library(yall)).
:- use_module(library(pairs)).
:- use_module(library(http/json)).

/* ============================== 1. LENGUAJE ============================== */

%  normalizar(+Texto, -Tokens)
%  Convierte el texto a una lista de átomos en minúsculas y sin tildes.
normalizar(Texto, Tokens) :-
    text_to_string(Texto, S0),
    string_lower(S0, S1),
    string_chars(S1, C1),
    maplist(limpiar_char, C1, C2),
    string_chars(S2, C2),
    split_string(S2, " ", " ", Partes),
    exclude(==(""), Partes, Partes1),
    maplist([P, A]>>atom_string(A, P), Partes1, Tokens).

limpiar_char(C, R) :- sin_tilde(C, R), !.
limpiar_char(C, C) :- char_type(C, alnum), !.
limpiar_char(_, ' ').

sin_tilde('á', a). sin_tilde('é', e). sin_tilde('í', i). sin_tilde('ó', o).
sin_tilde('ú', u). sin_tilde('ü', u). sin_tilde('ñ', n).
% Mayúsculas con tilde: string_lower/2 no las convierte si el sistema no usa un locale UTF-8.
sin_tilde('Á', a). sin_tilde('É', e). sin_tilde('Í', i). sin_tilde('Ó', o).
sin_tilde('Ú', u). sin_tilde('Ü', u). sin_tilde('Ñ', n).

%  Utilidades sobre la lista de tokens
tiene(T, P) :- memberchk(P, T).
tiene_alguno(T, Ps) :- member(P, Ps), memberchk(P, T), !.
tiene_prefijo(T, Pref) :- member(W, T), sub_atom(W, 0, _, _, Pref), !.
tiene_prefijo_alguno(T, Prefs) :- member(P, Prefs), tiene_prefijo(T, P), !.
tiene_frase(T, F) :- sublista(F, T, _), !.

sublista(Sub, L, Pos) :-
    Sub \== [],
    append(Pre, Resto, L),
    append(Sub, _, Resto),
    length(Pre, Pos).

/* ---------------------- detección de especies --------------------------- */

alias_tokens(Id, Toks) :-
    alias(Id, S),
    split_string(S, " ", "", Partes),
    maplist([P, A]>>atom_string(A, P), Partes, Toks).

%  especies_mencionadas(+Tokens, -Ids): especies nombradas, en orden de aparición.
%  Primero busca coincidencias exactas; si no hay, tolera un error de tipeo.
especies_mencionadas(Tokens, Ids) :-
    maplist(singular, Tokens, Singulares),
    findall(Pos-Id, ( member(Ts, [Tokens, Singulares]),
                      alias_tokens(Id, A), sublista(A, Ts, Pos) ), Exactas),
    (   Exactas \== []
    ->  Pares = Exactas
    ;   findall(Pos-Id, mencion_aproximada(Tokens, Id, Pos), Pares)
    ),
    keysort(Pares, Ordenados),
    pairs_values(Ordenados, Ids0),
    quitar_duplicados(Ids0, Ids).

%  singular(+Palabra, -Singular): "huemules" -> "huemul", "pumas" -> "puma".
singular(P, S) :- atom_length(P, L), L > 4, sub_atom(P, B, 2, 0, es), !, sub_atom(P, 0, B, _, S).
singular(P, S) :- atom_length(P, L), L > 3, sub_atom(P, B, 1, 0, s), !, sub_atom(P, 0, B, _, S).
singular(P, P).

mencion_aproximada(Tokens, Id, Pos) :-
    nth0(Pos, Tokens, T),
    atom_length(T, LT), LT >= 4,
    \+ palabra_comun(T),
    alias_tokens(Id, [A]),
    atom_length(A, LA), LA >= 5,
    distancia_uno(T, A).

%  distancia_uno(+A, +B): A y B difieren en exactamente una letra
%  (sustitución, inserción o borrado). Distancia de edición = 1.
distancia_uno(A, B) :-
    A \== B,
    atom_chars(A, X), atom_chars(B, Y),
    d1(X, Y), !.

d1([C|X], [C|Y]) :- !, d1(X, Y).
d1([_|X], [_|X]).
d1([_|X], X).
d1(X, [_|X]).

palabra_comun(P) :-
    memberchk(P, [bonito, bonita, guia, donde, cuando, comer, conocer, canto,
                  chacao, cuanto, cuantos, cuantas, poder]).

quitar_duplicados([], []).
quitar_duplicados([X|Xs], [X|Ys]) :-
    exclude(==(X), Xs, Xs1),
    quitar_duplicados(Xs1, Ys).

/* ---------------------- filtros (preguntas de listado) ------------------ */

filtros(T, Fs) :-
    findall(F, filtro(T, F), Fs0),
    quitar_duplicados(Fs0, Fs1),
    simplificar_filtros(Fs1, Fs).

% "en peligro" ya implica "amenazada": no se repite la condición.
simplificar_filtros(Fs0, Fs) :-
    (   memberchk(amenazada, Fs0),
        ( memberchk(en_peligro, Fs0) ; memberchk(estado(_), Fs0) )
    ->  exclude(==(amenazada), Fs0, Fs)
    ;   Fs = Fs0
    ).

filtro(T, clase(mamifero)) :- tiene_prefijo(T, mamifer).
filtro(T, clase(ave))      :- tiene_alguno(T, [ave, aves, pajaro, pajaros]).
filtro(T, clase(anfibio))  :- tiene_prefijo(T, anfibi).
filtro(T, zona(norte))     :- tiene(T, norte).
filtro(T, zona(centro))    :- tiene_alguno(T, [centro, central]).
filtro(T, zona(sur))       :- tiene(T, sur).
filtro(T, zona(austral))   :- tiene_alguno(T, [austral, patagonia, magallanes, aysen]).
filtro(T, eco(altiplano))          :- tiene(T, altiplano).
filtro(T, eco(cordillera_andina))  :- tiene_alguno(T, [cordillera, andes, montana, montanas]).
filtro(T, eco(bosque_templado))    :- tiene_prefijo(T, bosque).
filtro(T, eco(estepa_patagonica))  :- tiene(T, estepa).
filtro(T, eco(costa_marina))       :- tiene_alguno(T, [costa, costas, mar, marina, marino, marinos,
                                                       marinas, litoral, playa, playas, oceano]).
filtro(T, eco(rios_y_lagos))       :- tiene_alguno(T, [rio, rios, lago, lagos, dulce]).
filtro(T, eco(humedales))          :- tiene_alguno(T, [humedal, humedales, salar, salares, laguna, lagunas]).
filtro(T, eco(matorral_central))   :- tiene(T, matorral).
filtro(T, eco(desierto))           :- tiene_prefijo(T, desiert).
filtro(T, loc(chiloe))             :- tiene(T, chiloe).
filtro(T, loc(nahuelbuta))         :- tiene(T, nahuelbuta).
filtro(T, loc(torres_del_paine))   :- tiene(T, paine).
filtro(T, loc(lauca))              :- tiene_alguno(T, [lauca, chungara, putre]).
filtro(T, estado(cr)) :- tiene_frase(T, [peligro, critico]).
filtro(T, estado(nt)) :- tiene(T, casi), tiene_prefijo(T, amenazad).
filtro(T, estado(lc)) :- tiene_frase(T, [preocupacion, menor]).
filtro(T, estado(vu)) :- tiene_prefijo(T, vulnerable).
filtro(T, en_peligro) :- tiene_frase(T, [en, peligro]), \+ tiene_frase(T, [peligro, critico]).
filtro(T, amenazada)  :-
    once(( tiene_prefijo(T, amenazad) ; tiene_prefijo(T, extincion) ; tiene(T, riesgo) )),
    \+ tiene(T, casi).
filtro(T, endemica) :-
    once(( tiene_prefijo(T, endemic)
         ; tiene_frase(T, [solo, en, chile])
         ; tiene_frase(T, [solamente, en, chile])
         ; tiene_frase(T, [unicamente, en, chile])
         ; tiene_prefijo(T, exclusiv) )).
filtro(T, dieta(herbivoro))   :- tiene_prefijo(T, herbivor).
filtro(T, dieta(carnivoro))   :- tiene_prefijo(T, carnivor).
filtro(T, dieta(omnivoro))    :- tiene_prefijo(T, omnivor).
filtro(T, dieta(insectivoro)) :- tiene_prefijo(T, insectivor).
filtro(T, dieta(carronero))   :- tiene_prefijo(T, carroner).
filtro(T, alimento(A)) :- palabra_alimento(W, A), tiene(T, W).
filtro(T, emblema) :- tiene_prefijo_alguno(T, [emblem, escudo, simbol]).

palabra_alimento(peces, peces).        palabra_alimento(pescado, peces).
palabra_alimento(pescados, peces).     palabra_alimento(insectos, insectos).
palabra_alimento(insecto, insectos).   palabra_alimento(semillas, semillas).
palabra_alimento(frutos, frutos).      palabra_alimento(frutas, frutos).
palabra_alimento(roedores, roedores).  palabra_alimento(ratones, roedores).
palabra_alimento(crustaceos, crustaceos). palabra_alimento(hojas, hojas).
palabra_alimento(pasto, pasto).        palabra_alimento(algas, algas).
palabra_alimento(carrona, carrona).    palabra_alimento(moluscos, moluscos).
palabra_alimento(pinones, pinones).

cumple(X, clase(C))    :- clase(X, C).
cumple(X, zona(Z))     :- zona(X, Z).
cumple(X, eco(E))      :- ecosistema(X, E).
cumple(X, loc(L))      :- localidad(X, L).
cumple(X, estado(S))   :- conservacion(X, S).
cumple(X, en_peligro)  :- en_peligro(X).
cumple(X, amenazada)   :- amenazada(X).
cumple(X, endemica)    :- endemica_chile(X).
cumple(X, dieta(D))    :- dieta(X, D).
cumple(X, alimento(A)) :- come(X, A).
cumple(X, emblema)     :- emblema_nacional(X).

cumple_todos(X, Fs) :- forall(member(F, Fs), cumple(X, F)).

/* ---------------------- intenciones sobre una especie ------------------- */

intenciones(T, Is) :- findall(I, intencion(T, I), Is0), quitar_duplicados(Is0, Is).

intencion(T, cientifico) :- tiene_alguno(T, [cientifico, cientifica, latin]).
intencion(T, depredadores) :- pregunta_depredador(T).
intencion(T, dieta) :-
    \+ pregunta_depredador(T),
    tiene_alguno(T, [come, comen, alimenta, alimentan, alimentacion, dieta, comida,
                     alimento, alimentos, caza, cazan]).
intencion(T, habitat) :-
    tiene_alguno(T, [vive, viven, habita, habitan, habitat, donde, encuentra, encuentran,
                     encontrar, distribucion, zona, zonas, region, regiones,
                     ecosistema, ecosistemas, ver, observar]).
intencion(T, conservacion) :-
    once(( tiene_alguno(T, [estado, conservacion, peligro, extincion, uicn, riesgo, vulnerable])
         ; tiene_prefijo_alguno(T, [amenazad, protegid]) )).
intencion(T, amenazas) :-
    once(( tiene_frase(T, [por, que])
         ; tiene_alguno(T, [porque, amenaza, amenazas, causa, causas, problema, problemas,
                            afecta, afectan]) )).
intencion(T, endemico) :- filtro(T, endemica).
intencion(T, clase) :-
    \+ tiene_frase(T, [tipo, de, alimentacion]),
    \+ tiene_frase(T, [tipo, de, dieta]),
    tiene_alguno(T, [tipo, clase, grupo]).
intencion(T, verificar_clase(C)) :-
    \+ tiene_alguno(T, [tipo, clase, grupo]),
    filtro(T, clase(C)).
intencion(T, verificar_loc(L)) :- filtro(T, loc(L)).
intencion(T, verificar_zona(Z)) :- filtro(T, zona(Z)).
intencion(T, curioso) :-
    tiene_alguno(T, [curioso, curiosa, curiosidad, curiosidades, dato, datos,
                     interesante, sabias, particular]).
intencion(T, emblema) :- filtro(T, emblema).

%  "¿Quién se come AL pudú?", "¿Qué animales cazan A LA vicuña?", "depredadores"
pregunta_depredador(T) :-
    once(( tiene_prefijo(T, depreda)
         ; tiene_alguno(T, [presa, presas])
         ; tiene_prefijo_alguno(T, [come, caza]),
           ( tiene(T, al) ; tiene_frase(T, [a, la]) ; tiene_frase(T, [a, los]) ; tiene_frase(T, [a, las]) ) )).

/* ========================= 2. RESPONDER (núcleo) ========================= */

%  responder(+Pregunta, -Respuesta)  (Respuesta es un string)
responder(Pregunta, Respuesta) :-
    normalizar(Pregunta, T),
    (   T == []
    ->  R = 'Escribe una pregunta sobre fauna nativa de Chile. Por ejemplo: ¿Qué come el pudú?'
    ;   catch(responder_tokens(T, R), E,
              ( message_to_codes(E, R0), format(atom(R), 'Ocurrió un error interno: ~s', [R0]) ))
    ),
    contracciones(R, R1),
    atom_string(R1, Respuesta).

%  "de el" -> "del", "a el" -> "al" (contracciones obligatorias del español)
contracciones(A, R) :-
    atomic_list_concat(P1, ' de el ', A), atomic_list_concat(P1, ' del ', A1),
    atomic_list_concat(P2, ' a el ', A1), atomic_list_concat(P2, ' al ', R).

message_to_codes(E, Codes) :- format(codes(Codes), '~q', [E]).

responder_tokens(T, R) :-
    especies_mencionadas(T, Ids),
    (   Ids = [X, Y | _], pide_comparten(T)  -> resp_comparten(X, Y, R)
    ;   Ids = [X, Y | _], pide_comparar(T)   -> resp_comparar(X, Y, R)
    ;   Ids \== []                           -> resp_especies(Ids, T, R)
    ;   filtros(T, Fs), Fs \== []            -> resp_listado(T, Fs, R)
    ;   pide_todas(T)                        -> resp_listado(T, [], R)
    ;   menciona_zorro(T)                    -> resp_zorros(R)
    ;   social(T, R)                         -> true
    ;   resp_fuera_de_dominio(R)
    ).

pide_comparten(T) :- once(( tiene_prefijo(T, compart) ; tiene_alguno(T, [mismo, misma, juntos, juntas]) )).
pide_comparar(T) :-
    once(( tiene_prefijo_alguno(T, [compar, diferenci, distint, parec, semejan])
         ; tiene_alguno(T, [versus, vs, entre]) )).
pide_todas(T) :-
    tiene_alguno(T, [animales, especies, animal, especie, fauna]),
    tiene_alguno(T, [hay, conoces, todas, todos, lista, listar, cuales, cuantas, cuantos, tienes]).
menciona_zorro(T) :- tiene_alguno(T, [zorro, zorros]).

/* ---------------------- respuestas sobre especies ----------------------- */

resp_especies(Ids, T, R) :-
    intenciones(T, Is0),
    ( Is0 == [] -> Is = [ficha] ; Is = Is0 ),
    findall(Txt, (member(X, Ids), member(I, Is), texto(I, X, Txt)), Partes),
    atomic_list_concat(Partes, ' ', R).

texto(ficha, X, R) :-
    especie(X, _, Cient), clase(X, C), dieta(X, D),
    nom_cap(X, N), clase_con_articulo(C, CA), dieta_f(D, DF),
    lista_ecosistemas(X, Ecos), lista_zonas(X, Zonas),
    conservacion(X, S), nombre_estado(S, SN),
    format(atom(R0), '~w (~w) es ~w de dieta ~w. Vive en ~w (~w). Estado de conservación (UICN): ~w.',
           [N, Cient, CA, DF, Ecos, Zonas, SN]),
    ( endemica_chile(X) -> atom_concat(R0, ' Es una especie endémica de Chile.', R1) ; R1 = R0 ),
    ( dato_curioso(X, Dato) -> format(atom(R), '~w Dato curioso: ~w.', [R1, Dato]) ; R = R1 ).

texto(cientifico, X, R) :-
    especie(X, _, Cient), nom(X, N),
    format(atom(R), 'El nombre científico de ~w es ~w.', [N, Cient]).

texto(dieta, X, R) :-
    nom_cap(X, N), dieta(X, D), dieta_f(D, DF),
    findall(A, (come(X, Al), nombre_alimento_o_especie(Al, A)), As),
    lista_es(As, L),
    format(atom(R), '~w tiene una dieta ~w: se alimenta de ~w.', [N, DF, L]).

texto(habitat, X, R) :-
    nom_cap(X, N), lista_ecosistemas(X, Ecos), lista_zonas(X, Zonas),
    format(atom(R0), '~w vive en ~w, en la ~w.', [N, Ecos, Zonas]),
    findall(LN, (localidad(X, L), nombre_localidad(L, LN)), Ls),
    (   Ls == [] -> R = R0
    ;   lista_es(Ls, LL), format(atom(R), '~w Por ejemplo, se puede observar en ~w.', [R0, LL])
    ).

texto(conservacion, X, R) :-
    nom_cap(X, N), conservacion(X, S), nombre_estado(S, SN),
    (   amenazada(X)
    ->  Conc = 'por lo que es una especie amenazada'
    ;   Conc = 'por lo que no se considera una especie amenazada'
    ),
    format(atom(R), '~w tiene estado de conservación ~w según la Lista Roja de la UICN, ~w.', [N, SN, Conc]).

texto(amenazas, X, R) :-
    nom(X, N),
    findall(A, amenaza(X, A), As),
    (   As == []
    ->  format(atom(R), 'No tengo registradas amenazas específicas para ~w.', [N])
    ;   lista_es(As, L),
        format(atom(R), 'Las principales amenazas para ~w son: ~w.', [N, L])
    ).

texto(endemico, X, R) :-
    nom(X, N),
    (   endemica_chile(X)
    ->  format(atom(R), 'Sí, ~w es una especie endémica de Chile: solo vive en este país.', [N])
    ;   format(atom(R), 'No, según mi base de conocimiento ~w no está registrado como especie endémica de Chile.', [N])
    ).

texto(clase, X, R) :-
    nom_cap(X, N), clase(X, C), clase_con_articulo(C, CA),
    format(atom(R), '~w es ~w.', [N, CA]).

texto(verificar_clase(C2), X, R) :-
    nom(X, N), clase(X, C), clase_con_articulo(C, CA),
    (   C == C2
    ->  format(atom(R), 'Sí, ~w es ~w.', [N, CA])
    ;   clase_con_articulo(C2, CA2),
        format(atom(R), 'No, ~w no es ~w; es ~w.', [N, CA2, CA])
    ).

texto(verificar_loc(L), X, R) :-
    nom(X, N), nombre_localidad(L, LN),
    (   localidad(X, L)
    ->  format(atom(R), 'Sí, ~w se puede observar en ~w.', [N, LN])
    ;   format(atom(R), 'No tengo registrado que ~w se pueda observar en ~w.', [N, LN])
    ).

texto(verificar_zona(Z), X, R) :-
    nom(X, N), nombre_zona(Z, ZN), lista_zonas(X, Zs),
    (   zona(X, Z)
    ->  format(atom(R), 'Sí, ~w vive en la ~w (su distribución abarca la ~w).', [N, ZN, Zs])
    ;   format(atom(R), 'No, según mi base ~w no vive en la ~w; vive en la ~w.', [N, ZN, Zs])
    ).

texto(depredadores, X, R) :-
    nom(X, N),
    findall(PN, (depredador_de(P, X), nom(P, PN)), Ps),
    (   Ps == []
    ->  format(atom(R), 'No tengo registrados depredadores de ~w en mi base de conocimiento.', [N])
    ;   lista_es(Ps, L),
        format(atom(R), 'Según mi base de conocimiento, ~w es presa de ~w.', [N, L])
    ).

texto(curioso, X, R) :-
    nom(X, N),
    (   dato_curioso(X, D)
    ->  format(atom(R), 'Dato curioso sobre ~w: ~w.', [N, D])
    ;   format(atom(R), 'No tengo datos curiosos registrados sobre ~w.', [N])
    ).

texto(emblema, X, R) :-
    nom(X, N),
    (   emblema_nacional(X)
    ->  format(atom(R), 'Sí, ~w es un emblema nacional: aparece en el escudo de Chile.', [N])
    ;   findall(EN, (emblema_nacional(E), nom(E, EN)), Es), lista_es(Es, L),
        format(atom(R), 'No, ~w no aparece en el escudo de Chile; los animales del escudo son ~w.', [N, L])
    ).

resp_comparten(X, Y, R) :-
    nom(X, NX), nom(Y, NY),
    findall(HN, (habitat_comun(X, Y, H), nombre_ecosistema(H, HN)), Hs),
    findall(ZN, (zona(X, Z), zona(Y, Z), nombre_zona(Z, ZN)), Zs),
    (   Hs \== []
    ->  lista_es(Hs, LH),
        format(atom(R0), 'Sí, ~w y ~w comparten hábitat: ambos viven en ~w.', [NX, NY, LH])
    ;   lista_ecosistemas(X, EX), lista_ecosistemas(Y, EY),
        format(atom(R0), 'No, ~w y ~w no comparten ecosistema: el primero vive en ~w y el segundo en ~w.',
               [NX, NY, EX, EY])
    ),
    (   Zs == [] -> R = R0
    ;   lista_es(Zs, LZ), format(atom(R), '~w Coinciden en la ~w.', [R0, LZ])
    ).

resp_comparar(X, Y, R) :-
    linea_resumen(X, LX), linea_resumen(Y, LY),
    nom(X, NX), nom(Y, NY),
    findall(S, semejanza(X, Y, S), Ss),
    findall(D, diferencia(X, Y, D), Ds),
    format(atom(R0), 'Comparación entre ~w y ~w. ~w ~w', [NX, NY, LX, LY]),
    ( Ss == [] -> R1 = R0 ; lista_es(Ss, LS), format(atom(R1), '~w En común: ~w.', [R0, LS]) ),
    ( Ds == [] -> R = R1 ; lista_es(Ds, LD), format(atom(R), '~w Diferencias: ~w.', [R1, LD]) ).

linea_resumen(X, L) :-
    nom_cap(X, N), clase(X, C), clase_con_articulo(C, CA), dieta(X, D), dieta_f(D, DF),
    lista_ecosistemas(X, E), conservacion(X, S), nombre_estado(S, SN),
    format(atom(L), '~w es ~w de dieta ~w, vive en ~w y su estado es ~w.', [N, CA, DF, E, SN]).

semejanza(X, Y, S) :- clase(X, C), clase(Y, C), nombre_clase(C, _, P), format(atom(S), 'ambos son ~w', [P]).
semejanza(X, Y, S) :- dieta(X, D), dieta(Y, D), dieta_f(D, DF), format(atom(S), 'ambos tienen dieta ~w', [DF]).
semejanza(X, Y, S) :- conservacion(X, E), conservacion(Y, E), nombre_estado(E, EN),
                      format(atom(S), 'tienen el mismo estado de conservación (~w)', [EN]).
semejanza(X, Y, S) :- findall(HN, (habitat_comun(X, Y, H), nombre_ecosistema(H, HN)), Hs), Hs \== [],
                      lista_es(Hs, L), format(atom(S), 'comparten hábitat en ~w', [L]).

diferencia(X, Y, 'pertenecen a clases distintas') :- clase(X, C1), clase(Y, C2), C1 \== C2.
diferencia(X, Y, 'tienen dietas distintas') :- dieta(X, D1), dieta(Y, D2), D1 \== D2.
diferencia(X, Y, 'no comparten ecosistema') :- \+ habitat_comun(X, Y, _).
diferencia(X, Y, 'tienen distinto estado de conservación') :-
    conservacion(X, E1), conservacion(Y, E2), E1 \== E2.
diferencia(X, Y, S) :-
    endemica_chile(X), \+ endemica_chile(Y), nom(X, N),
    format(atom(S), 'solo ~w es endémico de Chile', [N]).
diferencia(X, Y, S) :-
    endemica_chile(Y), \+ endemica_chile(X), nom(Y, N),
    format(atom(S), 'solo ~w es endémico de Chile', [N]).

/* ------------------------- respuestas de listado ------------------------ */

resp_listado(T, Fs, R) :-
    findall(X, (especie(X, _, _), cumple_todos(X, Fs)), Xs),
    length(Xs, Total),
    ( Fs == [] -> Desc = 'forman parte de mi base de conocimiento' ; describir_filtros(Fs, Desc) ),
    (   Xs == []
    ->  format(atom(R), 'No encontré especies en mi base de conocimiento que ~w.', [Desc])
    ;   maplist(nom, Xs, Ns), lista_es(Ns, L),
        (   tiene_alguno(T, [cuantas, cuantos, cantidad, numero])
        ->  format(atom(R), 'Hay ~d especie(s) que ~w: ~w.', [Total, Desc, L])
        ;   format(atom(R), 'Especies que ~w: ~w. Total: ~d.', [Desc, L, Total])
        )
    ).

describir_filtros(Fs, D) :- maplist(desc_filtro, Fs, Ds), atomic_list_concat(Ds, ' y ', D).

desc_filtro(clase(C), D)    :- nombre_clase(C, _, P), format(atom(D), 'son ~w', [P]).
desc_filtro(zona(Z), D)     :- nombre_zona(Z, N), format(atom(D), 'viven en la ~w', [N]).
desc_filtro(eco(E), D)      :- nombre_ecosistema(E, N), format(atom(D), 'habitan en ~w', [N]).
desc_filtro(loc(L), D)      :- nombre_localidad(L, N), format(atom(D), 'se encuentran en ~w', [N]).
desc_filtro(estado(S), D)   :- nombre_estado(S, N), format(atom(D), 'tienen estado ~w', [N]).
desc_filtro(en_peligro, 'están en peligro (EN o CR)').
desc_filtro(amenazada, 'están amenazadas (VU, EN o CR)').
desc_filtro(endemica, 'son endémicas de Chile').
desc_filtro(dieta(Di), D)   :- dieta_f(Di, F), format(atom(D), 'tienen dieta ~w', [F]).
desc_filtro(alimento(A), D) :- nombre_alimento(A, N), format(atom(D), 'comen ~w', [N]).
desc_filtro(emblema, 'son emblemas del escudo nacional').

resp_zorros(R) :-
    findall(N, (alias(X, A), sub_string(A, 0, _, _, "zorro"), nom(X, N)), Ns0),
    quitar_duplicados(Ns0, Ns), lista_es(Ns, L),
    format(atom(R), 'En mi base hay varios zorros: ~w. ¿Sobre cuál quieres saber?', [L]).

/* ------------------------ conversación y ayuda --------------------------- */

social(T, R) :- tiene_alguno(T, [gracias, agradezco]), !,
    R = '¡De nada! Si quieres, pregúntame por otra especie de la fauna nativa de Chile.'.
social(T, R) :- tiene_alguno(T, [ayuda, ayudame, puedes, haces, funciona, funcionas]), !, ayuda(R).
social(T, R) :- tiene_alguno(T, [hola, buenas, buenos, saludos, hey]), !,
    ayuda(A), atom_concat('¡Hola! Soy un chatbot sobre fauna nativa de Chile. ', A, R).
social(T, R) :- tiene_alguno(T, [chao, adios, salir]), !,
    R = '¡Hasta luego! Cuida la fauna nativa.'.

ayuda('Puedo responder sobre 23 especies (mamíferos, aves y anfibios): qué comen, dónde viven, su estado de conservación, sus amenazas, si son endémicas, sus depredadores y datos curiosos. También puedo listar especies por zona, ecosistema, clase o estado, y comparar dos especies. Ejemplos: ¿Qué come el pudú? ¿Qué aves viven en el altiplano? ¿El puma y el guanaco comparten hábitat?').

resp_fuera_de_dominio(R) :-
    R = 'No tengo información sobre eso en mi base de conocimiento, que trata solo de fauna nativa de Chile. Prueba con preguntas como: ¿Dónde vive el huillín? o ¿Qué animales están en peligro?'.

/* ===================== 3. UTILIDADES DE REDACCIÓN ======================= */

genero(X, f) :- femenino(X), !.
genero(_, m).

nom(X, N) :- especie(X, Nombre, _), genero(X, G),
    ( G == f -> Art = la ; Art = el ), format(atom(N), '~w ~w', [Art, Nombre]).
nom_cap(X, N) :- nom(X, N0), capitalizar(N0, N).

capitalizar(A, C) :-
    sub_atom(A, 0, 1, _, F), sub_atom(A, 1, _, 0, Resto),
    upcase_atom(F, FU), atom_concat(FU, Resto, C).

clase_con_articulo(mamifero, 'un mamífero').
clase_con_articulo(ave, 'un ave').
clase_con_articulo(anfibio, 'un anfibio').

dieta_f(herbivoro, 'herbívora').
dieta_f(carnivoro, 'carnívora').
dieta_f(omnivoro, 'omnívora').
dieta_f(insectivoro, 'insectívora').
dieta_f(carronero, 'carroñera').

nombre_alimento_o_especie(A, N) :- especie(A, _, _), !, nom(A, N).
nombre_alimento_o_especie(A, N) :- nombre_alimento(A, N), !.
nombre_alimento_o_especie(A, A).

lista_ecosistemas(X, L) :-
    findall(N, (ecosistema(X, E), nombre_ecosistema(E, N)), Ns), lista_es(Ns, L).
lista_zonas(X, L) :-
    findall(N, (zona(X, Z), nombre_zona(Z, N)), Ns), lista_es(Ns, L).

%  lista_es(+Lista, -Atom): "a", "a y b", "a, b y c"
lista_es([], '').
lista_es([X], X) :- !.
lista_es(L, R) :-
    append(Init, [Ult], L), !,
    atomic_list_concat(Init, ', ', A),
    format(atom(R), '~w y ~w', [A, Ult]).

/* ======================== 4. INTERFAZ DE CONSOLA ======================== */

chat :-
    writeln('Chatbot de fauna nativa de Chile (Prolog). Escribe "salir" para terminar.'),
    chat_loop.

chat_loop :-
    write('Tú: '), flush_output,
    read_line_to_string(user_input, L),
    (   ( L == end_of_file ; normalizar(L, [salir]) )
    ->  writeln('Bot: ¡Hasta luego!')
    ;   responder(L, R), format('Bot: ~w~n', [R]), chat_loop
    ).

/* ================= 5. EXPORTAR LA BASE A JSON (para el LLM) ============= */

exportar_json :-
    findall(D, (especie(X, _, _), especie_dict(X, D)), Ds),
    json_write_dict(current_output,
        _{fuente: "Base de conocimiento Prolog (conocimiento.pl). Estados de conservación: Lista Roja UICN.",
          zonas: "zona norte = Arica y Parinacota a Coquimbo; zona centro = Valparaíso a Biobío; zona sur = La Araucanía a Los Lagos; zona austral = Aysén y Magallanes",
          especies: Ds},
        [width(0)]),
    nl.

especie_dict(X, _{id: XS, nombre: N, nombre_cientifico: C, clase: CL, dieta: DN,
                  alimentos: As, ecosistemas: Es, zonas: Zs, estado_conservacion: SN,
                  amenazada: Am, endemica_chile: En, localidades: Ls, amenazas: Ams,
                  emblema_nacional: Em, dato_curioso: Dc, presas_en_la_base: Ps,
                  depredadores_en_la_base: Dps, otros_nombres: Al}) :-
    especie(X, N0, C0), atom_string(X, XS), atom_string(N0, N), atom_string(C0, C),
    clase(X, Cl), nombre_clase(Cl, CL0, _), atom_string(CL0, CL),
    dieta(X, D), nombre_dieta(D, DN0), atom_string(DN0, DN),
    strs((come(X, A), nombre_alimento_o_especie(A, V0), quitar_articulo(V0, V)), V, As),
    strs((ecosistema(X, E), nombre_ecosistema(E, V)), V, Es),
    strs((zona(X, Z), nombre_zona(Z, V)), V, Zs),
    conservacion(X, S), nombre_estado(S, SN0), atom_string(SN0, SN),
    ( amenazada(X) -> Am = true ; Am = false ),
    ( endemica_chile(X) -> En = true ; En = false ),
    strs((localidad(X, L), nombre_localidad(L, V)), V, Ls),
    strs(amenaza(X, V), V, Ams),
    ( emblema_nacional(X) -> Em = true ; Em = false ),
    ( dato_curioso(X, Dc0) -> atom_string(Dc0, Dc) ; Dc = "" ),
    strs((depredador_de(X, P), especie(P, V, _)), V, Ps),
    strs((depredador_de(Q, X), especie(Q, V, _)), V, Dps),
    strs(alias(X, V), V, Al).

strs(Goal, V, L) :- findall(S, (Goal, atom_string(V, S)), L0), quitar_duplicados(L0, L).

quitar_articulo(V0, V) :-
    (   ( sub_atom(V0, 0, 3, _, 'el ') ; sub_atom(V0, 0, 3, _, 'la ') )
    ->  sub_atom(V0, 3, _, 0, V)
    ;   V = V0
    ).
