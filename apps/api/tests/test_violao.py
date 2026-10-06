import pytest

from music_tutor import teoria
from music_tutor.esquema import Aula
from music_tutor.render import renderizar
from music_tutor.validacao import validar_aula


def _aula(blocos, exemplos_extra=None):
    return Aula.model_validate({
        "codigo": "VI99",
        "assunto": "violao",
        "titulo": "Teste",
        "nivel": "iniciante",
        "resumo_curto": "Teste.",
        "prerequisitos": [],
        "objetivos": ["Testar"],
        "secoes": [{"titulo": "Seção", "blocos": blocos}],
        "exercicios": [],
        "resumo": ["Teste"],
        "pergunta_para_chat": "Teste?",
    })


def _acorde(cifra, casas, **extra):
    return {"tipo": "acorde", "cifra": cifra, "casas": casas, "legenda": cifra, **extra}


def test_notas_do_violao_seguem_a_afinacao_padrao():
    assert teoria.notas_do_violao([-1, 3, 2, 0, 1, 0]) == ["C4", "E4", "G4", "C5", "E5"]
    assert teoria.notas_do_violao([0, 0, 0, 0, 0, 0]) == list(teoria.CORDAS_VIOLAO)


@pytest.mark.parametrize("cifra, casas", [
    ("C", [-1, 3, 2, 0, 1, 0]), ("G", [3, 2, 0, 0, 0, 3]), ("D", [-1, -1, 0, 2, 3, 2]),
    ("Am", [-1, 0, 2, 2, 1, 0]), ("Em", [0, 2, 2, 0, 0, 0]), ("G7", [3, 2, 0, 0, 0, 1]),
    ("F", [1, 3, 3, 2, 1, 1]), ("Bm", [-1, 2, 4, 4, 3, 2]), ("C7M", [-1, 3, 2, 0, 0, 0]),
])
def test_acordes_abertos_conferem(cifra, casas):
    assert teoria.conferir_cifra(cifra, teoria.notas_do_violao(casas)) is None


def test_acorde_com_nota_errada_e_detectado():
    erro = teoria.conferir_cifra("C", teoria.notas_do_violao([0, 2, 2, 0, 0, 0]))
    assert erro and "Si" in erro


def test_acorde_sem_a_terca_e_detectado():
    erro = teoria.conferir_cifra("Am", teoria.notas_do_violao([-1, 0, 2, 2, -1, 0]))
    assert erro and "falta" in erro


def test_bloco_de_acorde_valida_dedos_e_pestana():
    ok = _aula([_acorde("F", [1, 3, 3, 2, 1, 1], dedos=[0, 3, 4, 2, 0, 0], pestana=1)])
    assert validar_aula(ok).ok, validar_aula(ok).erros
    sem_dedo = _aula([_acorde("C", [-1, 3, 2, 0, 1, 0], dedos=[0, 3, 0, 0, 1, 0])])
    assert any("sem dedo" in e for e in validar_aula(sem_dedo).erros)
    cifra_errada = _aula([_acorde("D", [-1, 3, 2, 0, 1, 0])])
    assert any("D não tem" in e for e in validar_aula(cifra_errada).erros)


def test_tablatura_fora_do_braco_e_detectada():
    exemplo = {"id": "ex", "titulo": "T", "legenda": "T", "tablatura": True,
               "eventos": [{"notas": ["C3"], "duracao": 4}]}
    r = validar_aula(_aula([{"tipo": "exemplo", "exemplo": exemplo}]))
    assert any("tablatura" in e for e in r.erros)


def test_aula_de_violao_abre_no_violao_com_diagrama():
    html = renderizar(_aula([_acorde("Em", [0, 2, 2, 0, 0, 0], dedos=[0, 2, 3, 0, 0, 0])]))
    assert 'aria-label="Diagrama do acorde Em"' in html
    assert 'data-tocar-acorde="a-0-0"' in html
    assert 'id="timbre-violao" data-timbre="violao" aria-pressed="true"' in html
    assert "Violão · Iniciante" in html
