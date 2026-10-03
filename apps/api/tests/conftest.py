from pathlib import Path

import pytest

from music_tutor.esquema import Aula

RAIZ = Path(__file__).resolve().parents[3]


@pytest.fixture
def aula_piloto() -> Aula:
    return Aula.model_validate_json((RAIZ / "aulas-exemplo" / "I08-intervalos-simples.json").read_text(encoding="utf-8"))


# Os testes procuram os itens pelo conteúdo, não pela posição, para a aula de exemplo poder mudar.

def primeiro_exemplo_com_intervalo(aula: Aula):
    return next(b.exemplo for s in aula.secoes for b in s.blocos if b.tipo == "exemplo" and b.exemplo.intervalo)


def escolha_sobre_intervalo(aula: Aula):
    return next(e for e in aula.exercicios if e.tipo == "multipla_escolha" and e.exemplo and e.exemplo.intervalo)


def exercicio_de_semitons(aula: Aula):
    return next(e for e in aula.exercicios if e.tipo == "multipla_escolha" and e.verificacao)


def teclado_re_quinta(aula: Aula):
    return next(e for e in aula.exercicios if e.tipo == "teclado" and e.nota_base == "D4" and e.intervalo == "5J")


@pytest.fixture
def aula_com_erro(aula_piloto) -> Aula:
    """Aula piloto com uma múltipla escolha apontando para a opção errada."""
    exe = escolha_sobre_intervalo(aula_piloto)
    exe.correta = (exe.correta + 1) % len(exe.opcoes)
    return aula_piloto
