import pytest

from music_tutor import teoria


@pytest.mark.parametrize(
    "de,para,codigo",
    [
        ("C4", "E4", "3M"),
        ("D4", "F4", "3m"),
        ("E4", "F4", "2m"),
        ("E4", "B4", "5J"),
        ("G4", "C5", "4J"),
        ("C4", "C5", "8J"),
        ("E4", "C4", "3M"),  # descendente: mesmo intervalo
        ("C4", "F#4", "4A"),
        ("C4", "Gb4", "5d"),
        ("A4", "C5", "3m"),
    ],
)
def test_calcular_intervalo(de, para, codigo):
    assert teoria.calcular_intervalo(de, para) == codigo


@pytest.mark.parametrize(
    "codigo,semitons,nome",
    [("2m", 1, "2ª menor"), ("3M", 4, "3ª maior"), ("4J", 5, "4ª justa"), ("5J", 7, "5ª justa"),
     ("6M", 9, "6ª maior"), ("7m", 10, "7ª menor"), ("8J", 12, "8ª justa"), ("1J", 0, "uníssono")],
)
def test_semitons_e_nomes(codigo, semitons, nome):
    assert teoria.semitons(codigo) == semitons
    assert teoria.nome_intervalo_pt(codigo) == nome


@pytest.mark.parametrize("codigo", ["3J", "5M", "9J", "16M", "4x", ""])
def test_codigos_invalidos(codigo):
    with pytest.raises(teoria.ErroTeoria):
        teoria.validar_codigo_intervalo(codigo)


def test_nota_por_intervalo():
    assert teoria.nota_por_intervalo("D4", "5J") == "A4"
    assert teoria.nota_por_intervalo("A4", "3m") == "C5"
    assert teoria.nota_por_intervalo("D4", "3M") == "F#4"
    assert teoria.nota_por_intervalo("C5", "3M", "abaixo") == "Ab4"


def test_nomes_em_portugues():
    assert teoria.nome_nota_pt("F#4") == "Fá♯"
    assert teoria.nome_nota_pt("Bb3", com_oitava=True) == "Si♭3"


def test_abc_com_acidentes_anacruse_e_volta_pelo_music21():
    eventos = [
        {"notas": ["G4"], "duracao": 0.75},
        {"notas": ["G4"], "duracao": 0.25},
        {"notas": ["D4", "F#4"], "duracao": 1},
        {"notas": ["D4", "F4"], "duracao": 1},
        {"notas": [], "duracao": 1},
        {"notas": ["C5"], "duracao": 3},
    ]
    abc = teoria.eventos_para_abc(eventos, compasso="3/4", anacruse=1)
    assert "G3/4G/4 |" in abc
    assert "[D=F]" in abc  # o bequadro cancela o sustenido do mesmo compasso
    assert teoria.alturas_do_abc(abc) == [[67], [67], [62, 66], [62, 65], [], [72]]


def test_evento_que_atravessa_a_barra():
    with pytest.raises(teoria.ErroTeoria):
        teoria.eventos_para_abc([{"notas": ["C4"], "duracao": 3}, {"notas": ["D4"], "duracao": 2}])


def test_abc_com_letra_sob_as_notas():
    eventos = [
        {"notas": ["D4"], "duracao": 0.5, "silaba": "Ci-"},
        {"notas": ["G4"], "duracao": 0.5, "silaba": "ran-"},
        {"notas": ["G4"], "duracao": 0.5, "silaba": "da"},
        {"notas": [], "duracao": 0.5},
        {"notas": ["B4"], "duracao": 0.5, "silaba": "de~o"},
    ]
    abc = teoria.eventos_para_abc(eventos, compasso="2/4", anacruse=0.5)
    assert abc.endswith("w:Ci-ran-da de~o\n")
    assert teoria.alturas_do_abc(abc) == [[62], [67], [67], [], [71]]


def test_abc_sem_letra_nao_tem_linha_w():
    assert "w:" not in teoria.eventos_para_abc([{"notas": ["C4"], "duracao": 4}])


@pytest.mark.parametrize(
    "armadura,esperado",
    [("C", {}), ("G", {"F": "#"}), ("D", {"F": "#", "C": "#"}), ("F", {"B": "b"}),
     ("Eb", {"B": "b", "E": "b", "A": "b"}), ("C#", {l: "#" for l in "FCGDAEB"})],
)
def test_acidentes_da_armadura(armadura, esperado):
    assert teoria.acidentes_da_armadura(armadura) == esperado


def test_armadura_invalida():
    with pytest.raises(teoria.ErroTeoria):
        teoria.acidentes_da_armadura("Am")


def test_abc_com_armadura_omite_acidente_da_armadura_e_marca_bequadro():
    eventos = [{"notas": ["G4"], "duracao": 1}, {"notas": ["F#4"], "duracao": 1},
               {"notas": ["F4"], "duracao": 1}, {"notas": ["F#5"], "duracao": 1}]
    abc = teoria.eventos_para_abc(eventos, armadura="G")
    assert "K:G" in abc and "G F =F f" in abc
    assert teoria.alturas_do_abc(abc) == [[67], [66], [65], [78]]


def test_abc_com_dinamica_acento_e_ligadura():
    eventos = [{"notas": ["C4"], "duracao": 2, "dinamica": "p"}, {"notas": ["D4"], "duracao": 1, "acento": True},
               {"notas": ["E4"], "duracao": 1, "ligada": True}, {"notas": ["E4"], "duracao": 4}]
    abc = teoria.eventos_para_abc(eventos)
    assert "!p!C2 !>!D E- | E4" in abc
    assert teoria.alturas_do_abc(abc) == [[60], [62], [64], [64]]


def test_abc_liga_so_a_nota_escolhida_do_acorde():
    eventos = [{"notas": ["C4", "E4", "G4", "C5"], "duracao": 2, "ligar": ["C5"]},
               {"notas": ["G3", "D4", "G4", "C5"], "duracao": 2}]
    abc = teoria.eventos_para_abc(eventos)
    assert "[CEGc-]2 [G,DGc]2" in abc
    assert teoria.alturas_do_abc(abc) == [[60, 64, 67, 72], [55, 62, 67, 72]]


def test_abc_em_clave_de_fa_mantem_a_altura():
    abc = teoria.eventos_para_abc([{"notas": ["F3"], "duracao": 2}, {"notas": ["C4"], "duracao": 2}], clave="fa")
    assert "clef=bass" in abc
    assert teoria.alturas_do_abc(abc) == [[53], [60]]


def test_abc_com_quialteras_de_tres():
    eventos = [{"notas": [n], "duracao": 1 / 3} for n in ("C4", "D4", "E4")] + [
        {"notas": ["F4"], "duracao": 1},
        {"notas": ["G4"], "duracao": 2 / 3}, {"notas": ["A4"], "duracao": 1 / 3}, {"notas": ["B4"], "duracao": 1},
    ]
    abc = teoria.eventos_para_abc(eventos)
    assert "(3:2:3C/2D/2E/2 F (3:2:2GA/2 B |]" in abc
    assert teoria.alturas_do_abc(abc) == [[60], [62], [64], [65], [67], [69], [71]]


def test_quialtera_incompleta():
    with pytest.raises(teoria.ErroTeoria):
        teoria.eventos_para_abc([{"notas": ["C4"], "duracao": 1 / 3}, {"notas": ["D4"], "duracao": 1 / 3},
                                 {"notas": ["E4"], "duracao": 1}])


def test_barras_de_colcheia_seguem_o_tempo_do_compasso():
    colcheias = [{"notas": ["C5"], "duracao": 0.5} for _ in range(6)]
    assert "c/2c/2 c/2c/2 c/2c/2 |]" in teoria.eventos_para_abc(colcheias, compasso="3/4")
    assert "c/2c/2c/2 c/2c/2c/2 |]" in teoria.eventos_para_abc(colcheias, compasso="6/8")
    pausa = [{"notas": ["C5"], "duracao": 0.5}, {"notas": [], "duracao": 0.5}, {"notas": ["C5"], "duracao": 1}]
    assert "c/2 z/2 c |]" in teoria.eventos_para_abc(pausa, compasso="2/4")


@pytest.mark.parametrize(
    "de, para, esperado",
    [("C4", "D5", "9M"), ("C4", "Db5", "9m"), ("D4", "F5", "10m"), ("E4", "A5", "11J"), ("C4", "A5", "13M")],
)
def test_intervalo_composto(de, para, esperado):
    assert teoria.calcular_intervalo_composto(de, para) == esperado
    assert teoria.calcular_intervalo(de, para) == esperado.replace(esperado[:-1], str(int(esperado[:-1]) - 7))


def test_codigos_compostos():
    assert teoria.semitons("10M") == 16 and teoria.nome_intervalo_pt("11J") == "11ª justa"
    assert teoria.nota_por_intervalo("C4", "9M") == "D5"
    with pytest.raises(teoria.ErroTeoria):
        teoria.validar_codigo_intervalo("9J")


def test_armadura_nao_repete_o_acidente_no_compasso():
    eventos = [{"notas": ["F#4"], "duracao": 1}, {"notas": ["F#4"], "duracao": 1},
               {"notas": ["F4"], "duracao": 1}, {"notas": ["F#4"], "duracao": 1}]
    abc = teoria.eventos_para_abc(eventos, armadura="D")
    assert "F F =F ^F |]" in abc
    assert teoria.alturas_do_abc(abc) == [[66], [66], [65], [66]]
