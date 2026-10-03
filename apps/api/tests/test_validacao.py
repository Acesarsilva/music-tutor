from music_tutor.validacao import validar_aula


def test_aula_piloto_passa(aula_piloto):
    r = validar_aula(aula_piloto)
    assert r.ok, r.erros
    assert len(r.exercicios) == len(aula_piloto.exercicios)
    teclado = next(e for e in r.exercicios if e["tipo"] == "teclado")
    assert teclado["alvo"] == 69 and teclado["alvo_nome"] == "Lá"


def test_intervalo_afirmado_errado_e_detectado(aula_piloto):
    exemplo = aula_piloto.secoes[0].blocos[1].exemplo
    exemplo.intervalo.codigo = "3m"  # Dó-Mi é 3ª maior
    r = validar_aula(aula_piloto)
    assert any("não 3m" in e for e in r.erros)


def test_resposta_errada_de_multipla_escolha_e_detectada(aula_piloto):
    aula_piloto.exercicios[1].correta = 2  # aponta para "3ª maior", mas Ré-Fá é 3ª menor
    r = validar_aula(aula_piloto)
    assert any("deveria ser '3ª menor'" in e for e in r.erros)


def test_semitons_errados_sao_detectados(aula_piloto):
    aula_piloto.exercicios[0].correta = 1  # "3 semitons" para uma 3ª maior
    r = validar_aula(aula_piloto)
    assert any("tem 4 semitons" in e for e in r.erros)


def test_nota_invalida(aula_piloto):
    aula_piloto.secoes[0].blocos[1].exemplo.eventos[0].notas = ["H4"]
    r = validar_aula(aula_piloto)
    assert any("nota inválida" in e for e in r.erros)


def test_tecla_fora_do_teclado(aula_piloto):
    exe = aula_piloto.exercicios[5]
    exe.ate = "G4"  # Ré + 5ª justa = Lá4, fora
    r = validar_aula(aula_piloto)
    assert any("fora do teclado" in e for e in r.erros)
