from types import SimpleNamespace

import pytest

from music_tutor import gerador


class _Stream:
    def __init__(self, resposta):
        self.resposta = resposta

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return self.resposta


class ClienteFalso:
    """Imita client.beta.messages.stream devolvendo respostas pré-definidas."""

    def __init__(self, aulas):
        self.aulas = list(aulas)
        self.chamadas = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **kwargs):
        self.chamadas.append(kwargs)
        aula = self.aulas.pop(0)
        return _Stream(SimpleNamespace(stop_reason="end_turn", parsed_output=aula, content=[{"type": "text", "text": "{}"}]))


def test_gera_e_valida(aula_piloto):
    cliente = ClienteFalso([aula_piloto])
    aula = gerador.gerar_aula("I08", cliente=cliente)
    assert aula.codigo == "I08"
    chamada = cliente.chamadas[0]
    assert chamada["model"] == gerador.MODELO_PADRAO
    assert chamada["output_format"] is gerador.Aula
    assert "<modulo>" in chamada["messages"][0]["content"]


def test_devolve_erros_ao_modelo_e_aceita_correcao(aula_piloto):
    errada = aula_piloto.model_copy(deep=True)
    errada.exercicios[1].correta = 0
    cliente = ClienteFalso([errada, aula_piloto])
    gerador.gerar_aula("I08", cliente=cliente)
    assert len(cliente.chamadas) == 2
    ultima = cliente.chamadas[1]["messages"]
    assert ultima[-1]["role"] == "user" and "music21" in ultima[-1]["content"]


def test_desiste_depois_das_tentativas(aula_piloto):
    errada = aula_piloto.model_copy(deep=True)
    errada.exercicios[1].correta = 0
    cliente = ClienteFalso([errada] * (gerador.TENTATIVAS_DE_CORRECAO + 1))
    with pytest.raises(RuntimeError, match="não passou na validação"):
        gerador.gerar_aula("I08", cliente=cliente)


def test_modulo_inexistente():
    with pytest.raises(FileNotFoundError):
        gerador.carregar_modulo("Z99")
