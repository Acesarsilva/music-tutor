"""Confere a teoria de uma aula com music21 e prepara os dados que o HTML usa.

Tudo que o aluno vê como certo (intervalos afirmados, respostas, semitons) é recalculado
aqui. Se algo não bate, a aula volta ao Claude com a lista de erros.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field

from . import teoria
from .esquema import (
    Aula,
    BlocoExemplo,
    BlocoTabela,
    BlocoTeclado,
    Exemplo,
    ExercicioMultipla,
    ExercicioPercepcao,
    ExercicioTeclado,
)


@dataclass
class Resultado:
    erros: list[str] = field(default_factory=list)
    exemplos: dict[str, dict] = field(default_factory=dict)
    exercicios: list[dict] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.erros


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKC", texto).strip().lower()
    return texto.replace("º", "ª").replace(" ", " ")


def _checar_nota(nota: str, onde: str, r: Resultado) -> bool:
    try:
        teoria.para_pitch(nota)
        return True
    except teoria.ErroTeoria as e:
        r.erros.append(f"{onde}: {e}")
        return False


def _compilar_exemplo(ex: Exemplo, onde: str, r: Resultado) -> None:
    if ex.id in r.exemplos:
        r.erros.append(f"{onde}: id de exemplo repetido {ex.id!r}")
        return
    if not ex.eventos:
        r.erros.append(f"{onde}: exemplo sem eventos")
        return
    notas_ok = all(_checar_nota(n, f"{onde}.eventos", r) for ev in ex.eventos for n in ev.notas)
    if not notas_ok:
        return
    eventos = [ev.model_dump() for ev in ex.eventos]
    try:
        abc = teoria.eventos_para_abc(
            eventos, compasso=ex.compasso, anacruse=ex.anacruse, clave=ex.clave
        )
    except teoria.ErroTeoria as e:
        r.erros.append(f"{onde}: {e}")
        return

    esperado = [sorted(teoria.midi(n) for n in ev.notas) for ev in ex.eventos]
    lido = teoria.alturas_do_abc(abc)
    if lido != esperado:
        r.erros.append(f"{onde}: a partitura gerada não corresponde às notas (lido {lido}, esperado {esperado})")
        return

    if ex.intervalo is not None:
        afirmado = ex.intervalo
        if _checar_nota(afirmado.de, f"{onde}.intervalo.de", r) and _checar_nota(
            afirmado.para, f"{onde}.intervalo.para", r
        ):
            try:
                real = teoria.calcular_intervalo(afirmado.de, afirmado.para)
                teoria.validar_codigo_intervalo(afirmado.codigo)
            except teoria.ErroTeoria as e:
                r.erros.append(f"{onde}.intervalo: {e}")
            else:
                if real != afirmado.codigo:
                    r.erros.append(
                        f"{onde}.intervalo: {afirmado.de}-{afirmado.para} é {teoria.nome_intervalo_pt(real)}, "
                        f"não {afirmado.codigo}"
                    )
                presentes = {teoria.midi(n) for ev in ex.eventos for n in ev.notas}
                if teoria.midi(afirmado.de) not in presentes or teoria.midi(afirmado.para) not in presentes:
                    r.erros.append(f"{onde}.intervalo: as notas {afirmado.de} e {afirmado.para} não estão no exemplo")

    r.exemplos[ex.id] = {
        "id": ex.id,
        "titulo": ex.titulo,
        "legenda": ex.legenda,
        "abc": abc,
        "andamento": ex.andamento,
        "eventos": [{"midis": m, "duracao": ev.duracao} for m, ev in zip(esperado, ex.eventos)],
    }


def _checar_opcoes(opcoes: list[str], correta: int, onde: str, r: Resultado) -> bool:
    if not 2 <= len(opcoes) <= 5:
        r.erros.append(f"{onde}: use de 2 a 5 opções (tem {len(opcoes)})")
        return False
    if len({_normalizar(o) for o in opcoes}) != len(opcoes):
        r.erros.append(f"{onde}: há opções repetidas")
        return False
    if not 0 <= correta < len(opcoes):
        r.erros.append(f"{onde}: índice da opção correta fora do intervalo")
        return False
    return True


def _checar_resposta_intervalo(ex: Exemplo, opcoes: list[str], correta: int, onde: str, r: Resultado) -> None:
    if ex.intervalo is None:
        return
    try:
        nome = teoria.nome_intervalo_pt(ex.intervalo.codigo)
    except teoria.ErroTeoria:
        return  # já reportado no exemplo
    if _normalizar(opcoes[correta]) != _normalizar(nome):
        r.erros.append(f"{onde}: a opção correta deveria ser {nome!r}, mas é {opcoes[correta]!r}")


def validar_aula(aula: Aula) -> Resultado:
    r = Resultado()

    for i, secao in enumerate(aula.secoes):
        for j, bloco in enumerate(secao.blocos):
            onde = f"secoes[{i}].blocos[{j}]"
            if isinstance(bloco, BlocoExemplo):
                _compilar_exemplo(bloco.exemplo, onde, r)
            elif isinstance(bloco, BlocoTabela):
                for k, linha in enumerate(bloco.linhas):
                    if len(linha) != len(bloco.cabecalho):
                        r.erros.append(f"{onde}.linhas[{k}]: {len(linha)} colunas, cabeçalho tem {len(bloco.cabecalho)}")
            elif isinstance(bloco, BlocoTeclado):
                if all(_checar_nota(n, onde, r) for n in [bloco.de, bloco.ate, *bloco.destaque]):
                    lo, hi = teoria.midi(bloco.de), teoria.midi(bloco.ate)
                    fora = [n for n in bloco.destaque if not lo <= teoria.midi(n) <= hi]
                    if fora:
                        r.erros.append(f"{onde}: notas fora do teclado mostrado: {fora}")

    for i, exe in enumerate(aula.exercicios):
        onde = f"exercicios[{i}]"
        compilado: dict = {"indice": i, "tipo": exe.tipo, "conceito": exe.conceito}
        if isinstance(exe, (ExercicioMultipla, ExercicioPercepcao)):
            if exe.exemplo is not None:
                _compilar_exemplo(exe.exemplo, f"{onde}.exemplo", r)
                compilado["exemplo"] = exe.exemplo.id
            if _checar_opcoes(exe.opcoes, exe.correta, onde, r):
                if exe.exemplo is not None:
                    _checar_resposta_intervalo(exe.exemplo, exe.opcoes, exe.correta, onde, r)
                if isinstance(exe, ExercicioMultipla) and exe.verificacao is not None:
                    try:
                        valor = teoria.semitons(exe.verificacao.intervalo)
                    except teoria.ErroTeoria as e:
                        r.erros.append(f"{onde}.verificacao: {e}")
                    else:
                        numeros = [int(t) for t in exe.opcoes[exe.correta].split() if t.isdigit()]
                        if numeros != [valor]:
                            r.erros.append(
                                f"{onde}: {teoria.nome_intervalo_pt(exe.verificacao.intervalo)} tem {valor} semitons, "
                                f"mas a opção correta é {exe.opcoes[exe.correta]!r}"
                            )
            if isinstance(exe, ExercicioPercepcao) and exe.exemplo.intervalo is None:
                r.erros.append(f"{onde}: exercício de percepção precisa do intervalo afirmado no exemplo")
            compilado["correta"] = exe.correta
        elif isinstance(exe, ExercicioTeclado):
            if all(_checar_nota(n, onde, r) for n in [exe.nota_base, exe.de, exe.ate]):
                try:
                    alvo = teoria.nota_por_intervalo(exe.nota_base, exe.intervalo, exe.direcao)
                except teoria.ErroTeoria as e:
                    r.erros.append(f"{onde}: {e}")
                else:
                    lo, hi = teoria.midi(exe.de), teoria.midi(exe.ate)
                    for n in (exe.nota_base, alvo):
                        if not lo <= teoria.midi(n) <= hi:
                            r.erros.append(f"{onde}: a nota {n} fica fora do teclado ({exe.de} a {exe.ate})")
                    compilado.update(
                        base=teoria.midi(exe.nota_base),
                        alvo=teoria.midi(alvo),
                        alvo_nome=teoria.nome_nota_pt(alvo),
                        intervalo_nome=teoria.nome_intervalo_pt(exe.intervalo),
                    )
        r.exercicios.append(compilado)

    return r
