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


@pytest.mark.parametrize("codigo", ["3J", "5M", "9M", "4x", ""])
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
    assert "G3/4 G/4 |" in abc
    assert "[D=F]" in abc  # o bequadro cancela o sustenido do mesmo compasso
    assert teoria.alturas_do_abc(abc) == [[67], [67], [62, 66], [62, 65], [], [72]]


def test_evento_que_atravessa_a_barra():
    with pytest.raises(teoria.ErroTeoria):
        teoria.eventos_para_abc([{"notas": ["C4"], "duracao": 3}, {"notas": ["D4"], "duracao": 2}])
