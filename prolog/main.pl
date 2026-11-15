:- encoding(utf8).
/*  Punto de entrada por línea de comandos.
      swipl main.pl                    -> chat interactivo en consola
      swipl main.pl "¿Qué come el pudú?" -> responde una pregunta
      swipl main.pl --stdin            -> lee la pregunta desde la entrada estándar (lo usa Python)
      swipl main.pl --json             -> exporta la base de conocimiento en JSON (lo usa el LLM)
*/
:- initialization(main, main).
:- ensure_loaded(chatbot).

main :-
    set_stream(user_output, encoding(utf8)),
    set_stream(user_input, encoding(utf8)),
    current_prolog_flag(argv, Argv),
    (   Argv == ['--json']  -> exportar_json
    ;   Argv == ['--stdin'] -> read_string(user_input, _, Q), responder(Q, R), writeln(R)
    ;   Argv == []          -> chat
    ;   atomic_list_concat(Argv, ' ', Q), responder(Q, R), writeln(R)
    ).
