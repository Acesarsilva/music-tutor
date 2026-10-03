from conftest import (
    escolha_sobre_intervalo,
    exercicio_de_semitons,
    primeiro_exemplo_com_intervalo,
    teclado_re_quinta,
)
from music_tutor.validacao import validar_aula


def test_aula_piloto_passa(aula_piloto):
    r = validar_aula(aula_piloto)
    assert r.ok, r.erros
    assert len(r.exercicios) == len(aula_piloto.exercicios)
    teclado = next(e for e in r.exercicios if e["tipo"] == "teclado")
    assert teclado["alvo"] == 69 and teclado["alvo_nome"] == "Lá"


def test_intervalo_afirmado_errado_e_detectado(aula_piloto):
    exemplo = primeiro_exemplo_com_intervalo(aula_piloto)
    exemplo.intervalo.codigo = "7M"  # nenhum exemplo da aula é uma 7ª maior
    r = validar_aula(aula_piloto)
    assert any("não 7M" in e for e in r.erros)


def test_resposta_errada_de_multipla_escolha_e_detectada(aula_piloto):
    exe = escolha_sobre_intervalo(aula_piloto)
    certa = exe.opcoes[exe.correta]
    exe.correta = (exe.correta + 1) % len(exe.opcoes)
    r = validar_aula(aula_piloto)
    assert any(f"deveria ser '{certa}'" in e for e in r.erros)


def test_semitons_errados_sao_detectados(aula_piloto):
    exe = exercicio_de_semitons(aula_piloto)
    exe.correta = (exe.correta + 1) % len(exe.opcoes)
    r = validar_aula(aula_piloto)
    assert any("semitons" in e for e in r.erros)


def test_nota_invalida(aula_piloto):
    primeiro_exemplo_com_intervalo(aula_piloto).eventos[0].notas = ["H4"]
    r = validar_aula(aula_piloto)
    assert any("nota inválida" in e for e in r.erros)


def test_tecla_fora_do_teclado(aula_piloto):
    exe = teclado_re_quinta(aula_piloto)
    exe.ate = "G4"  # Ré + 5ª justa = Lá4, fora
    r = validar_aula(aula_piloto)
    assert any("fora do teclado" in e for e in r.erros)


def test_nota_fora_do_braco_do_violao(aula_piloto):
    exe = teclado_re_quinta(aula_piloto)
    exe.nota_base, exe.de, exe.ate = "C3", "C3", "C6"  # Dó3 escrito fica abaixo da corda Mi solta
    r = validar_aula(aula_piloto)
    assert any("fora do braço do violão" in e for e in r.erros)
