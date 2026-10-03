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


def test_percepcao_aceita_tom_e_semitom_como_nome(aula_piloto):
    from music_tutor.esquema import Exemplo, ExercicioPercepcao, IntervaloAfirmado

    exemplo = Exemplo(
        id="ex-mi-fa", titulo="?", legenda="Mi e Fá.",
        eventos=[{"notas": ["E4"], "duracao": 2}, {"notas": ["F4"], "duracao": 2}],
        intervalo=IntervaloAfirmado(de="E4", para="F4", codigo="2m"),
    )
    exe = ExercicioPercepcao(
        tipo="percepcao", enunciado="Tom ou semitom?", exemplo=exemplo, opcoes=["tom", "semitom"],
        correta=1, explicacao="Mi–Fá é semitom.", conceito="semitom",
    )
    aula_piloto.exercicios.append(exe)
    assert validar_aula(aula_piloto).ok
    exe.correta = 0
    assert any("deveria ser" in e for e in validar_aula(aula_piloto).erros)


def _aula_com_exemplo(aula, eventos):
    from music_tutor.esquema import BlocoExemplo, Exemplo

    exemplo = Exemplo(id="ex-teste", titulo="t", legenda="l", eventos=eventos)
    aula.secoes[0].blocos.append(BlocoExemplo(tipo="exemplo", exemplo=exemplo))
    return validar_aula(aula)


def test_dinamica_vale_ate_a_proxima_e_vira_intensidade(aula_piloto):
    r = _aula_com_exemplo(aula_piloto, [
        {"notas": ["C4"], "duracao": 1, "dinamica": "p"}, {"notas": ["D4"], "duracao": 1},
        {"notas": ["E4"], "duracao": 1, "dinamica": "f", "acento": True}, {"notas": ["F4"], "duracao": 1},
    ])
    assert r.ok, r.erros
    assert [e["intensidade"] for e in r.exemplos["ex-teste"]["eventos"]] == [0.38, 0.38, 1.0, 0.82]


def test_ligadura_exige_mesmas_notas(aula_piloto):
    r = _aula_com_exemplo(aula_piloto, [
        {"notas": ["C4"], "duracao": 2, "ligada": True}, {"notas": ["D4"], "duracao": 2},
    ])
    assert any("ligadura" in e for e in r.erros)


def test_acento_se_destaca_das_vizinhas(aula_piloto):
    r = _aula_com_exemplo(aula_piloto, [
        {"notas": ["C5"], "duracao": 1, "acento": True}, {"notas": ["C5"], "duracao": 1},
    ])
    assert [e["intensidade"] for e in r.exemplos["ex-teste"]["eventos"]] == [0.91, 0.66]


def test_forquilha_interpola_e_staccato_passa_para_o_audio(aula_piloto):
    r = _aula_com_exemplo(aula_piloto, [
        {"notas": ["C4"], "duracao": 1, "dinamica": "p", "forquilha": "crescendo", "staccato": True},
        {"notas": ["D4"], "duracao": 1, "expressao": "inicio"}, {"notas": ["E4"], "duracao": 1, "expressao": "fim"},
        {"notas": ["F4"], "duracao": 1, "dinamica": "f", "forquilha": "fim"},
    ])
    assert r.ok, r.erros
    eventos = r.exemplos["ex-teste"]["eventos"]
    assert [e["intensidade"] for e in eventos] == [0.38, 0.53, 0.67, 0.82]
    assert eventos[0]["staccato"] and "!p!!<(!.C" in r.exemplos["ex-teste"]["abc"]


def test_forquilha_sem_dinamica_de_chegada(aula_piloto):
    r = _aula_com_exemplo(aula_piloto, [
        {"notas": ["C4"], "duracao": 2, "dinamica": "p", "forquilha": "crescendo"},
        {"notas": ["D4"], "duracao": 2, "forquilha": "fim"},
    ])
    assert any("dinâmica de chegada" in e for e in r.erros)


def test_intervalo_composto_afirmado_confere_sem_reduzir(aula_piloto):
    exemplo = primeiro_exemplo_com_intervalo(aula_piloto)
    exemplo.eventos[0].notas, exemplo.eventos[1].notas = ["C4"], ["E5"]
    exemplo.intervalo.de, exemplo.intervalo.para = "C4", "E5"
    exemplo.intervalo.codigo = "10M"
    assert not any(".intervalo" in e for e in validar_aula(aula_piloto).erros)
    exemplo.intervalo.codigo = "3M"  # até a 8ª, vale o intervalo simples
    assert not any(".intervalo" in e for e in validar_aula(aula_piloto).erros)
    exemplo.intervalo.codigo = "10m"
    assert any("é 10ª maior, não 10m" in e for e in validar_aula(aula_piloto).erros)
