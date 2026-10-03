"""Funções de teoria musical usadas para validar aulas e gerar notação.

Notas são escritas em notação científica com acidentes ASCII: "C4", "F#4", "Bb3".
Intervalos usam códigos curtos em português: número + qualidade
(J = justo, M = maior, m = menor, A = aumentado, d = diminuto), por exemplo "3M", "5J".
"""

from __future__ import annotations

import re
from fractions import Fraction

from music21 import converter, interval, pitch

_NOTA_RE = re.compile(r"^([A-G])(##|#|bb|b)?(-?\d)$")

_NOMES_PT = {"C": "Dó", "D": "Ré", "E": "Mi", "F": "Fá", "G": "Sol", "A": "Lá", "B": "Si"}
_ACIDENTES_PT = {"": "", "#": "♯", "##": "𝄪", "b": "♭", "bb": "𝄫"}
_ACIDENTES_ABC = {"": "", "#": "^", "##": "^^", "b": "_", "bb": "__"}

_QUALIDADE_PARA_M21 = {"J": "P", "M": "M", "m": "m", "A": "A", "d": "d"}
_QUALIDADE_DE_M21 = {v: k for k, v in _QUALIDADE_PARA_M21.items()}
_QUALIDADE_PT = {
    "J": "justa",
    "M": "maior",
    "m": "menor",
    "A": "aumentada",
    "d": "diminuta",
}
_CODIGO_RE = re.compile(r"^([1-8])(J|M|m|A|d)$")


class ErroTeoria(ValueError):
    """Nota, intervalo ou trecho musical inválido."""


def _partes(nota: str) -> tuple[str, str, int]:
    m = _NOTA_RE.match(nota)
    if not m:
        raise ErroTeoria(f"nota inválida: {nota!r} (use o formato C4, F#4, Bb3)")
    letra, acidente, oitava = m.group(1), m.group(2) or "", int(m.group(3))
    return letra, acidente, oitava


def para_pitch(nota: str) -> pitch.Pitch:
    letra, acidente, oitava = _partes(nota)
    return pitch.Pitch(letra + acidente.replace("b", "-") + str(oitava))


def midi(nota: str) -> int:
    return int(para_pitch(nota).midi)


def nome_nota_pt(nota: str, com_oitava: bool = False) -> str:
    """"F#4" -> "Fá♯" (ou "Fá♯4" com a oitava)."""
    letra, acidente, oitava = _partes(nota)
    nome = _NOMES_PT[letra] + _ACIDENTES_PT[acidente]
    return f"{nome}{oitava}" if com_oitava else nome


def validar_codigo_intervalo(codigo: str) -> tuple[int, str]:
    m = _CODIGO_RE.match(codigo)
    if not m:
        raise ErroTeoria(f"código de intervalo inválido: {codigo!r} (ex.: 3M, 5J, 2m)")
    numero, qualidade = int(m.group(1)), m.group(2)
    justos = {1, 4, 5, 8}
    if qualidade == "J" and numero not in justos:
        raise ErroTeoria(f"{numero}ª não pode ser justa")
    if qualidade in "Mm" and numero in justos:
        raise ErroTeoria(f"{numero}ª não pode ser maior nem menor")
    return numero, qualidade


def nome_intervalo_pt(codigo: str) -> str:
    """"3M" -> "3ª maior"; "5J" -> "5ª justa"; "1J" -> "uníssono"."""
    numero, qualidade = validar_codigo_intervalo(codigo)
    if codigo == "1J":
        return "uníssono"
    return f"{numero}ª {_QUALIDADE_PT[qualidade]}"


def _para_m21(codigo: str) -> interval.Interval:
    numero, qualidade = validar_codigo_intervalo(codigo)
    return interval.Interval(f"{_QUALIDADE_PARA_M21[qualidade]}{numero}")


def semitons(codigo: str) -> int:
    return int(_para_m21(codigo).semitones)


def calcular_intervalo(de: str, para: str) -> str:
    """Intervalo simples entre duas notas, sem direção: ("D4", "F4") -> "3m"."""
    i = interval.Interval(para_pitch(de), para_pitch(para))
    nome = i.semiSimpleName  # mantém a 8ª como 8ª
    m = re.match(r"^(P|M|m|A|d)(\d+)$", nome)
    if not m or int(m.group(2)) > 8:
        raise ErroTeoria(f"intervalo {de}-{para} ({nome}) fora do escopo de intervalos simples")
    return f"{m.group(2)}{_QUALIDADE_DE_M21[m.group(1)]}"


def nota_por_intervalo(base: str, codigo: str, direcao: str = "acima") -> str:
    """Nota que forma o intervalo com a base: ("D4", "5J") -> "A4"."""
    i = _para_m21(codigo)
    if direcao == "abaixo":
        i = i.reverse()
    elif direcao != "acima":
        raise ErroTeoria(f"direção inválida: {direcao!r}")
    p = i.transposePitch(para_pitch(base))
    acidente = {None: "", "sharp": "#", "double-sharp": "##", "flat": "b", "double-flat": "bb", "natural": ""}
    nome_acidente = p.accidental.name if p.accidental is not None else None
    if nome_acidente not in acidente:
        raise ErroTeoria(f"acidente não suportado: {nome_acidente}")
    return f"{p.step}{acidente[nome_acidente]}{p.octave}"


# ---------------------------------------------------------------- ABC

def _duracao_abc(beats: Fraction) -> str:
    """Duração em tempos (semínima = 1) -> sufixo ABC com L:1/4."""
    if beats <= 0:
        raise ErroTeoria("duração deve ser positiva")
    if beats == 1:
        return ""
    if beats.denominator == 1:
        return str(beats.numerator)
    if beats.numerator == 1:
        return f"/{beats.denominator}"
    return f"{beats.numerator}/{beats.denominator}"


# Armaduras de clave aceitas (tonalidades maiores, até 7 acidentes) e as notas que cada uma altera.
_ORDEM_SUSTENIDOS = "FCGDAEB"
_ORDEM_BEMOIS = "BEADGCF"
_ARMADURAS = {
    **{t: n for n, t in enumerate(["C", "G", "D", "A", "E", "B", "F#", "C#"])},
    **{t: -n for n, t in enumerate(["C", "F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb"])},
}


def acidentes_da_armadura(armadura: str) -> dict[str, str]:
    """"D" -> {"F": "#", "C": "#"}; "Bb" -> {"B": "b", "E": "b"}."""
    if armadura not in _ARMADURAS:
        raise ErroTeoria(f"armadura inválida: {armadura!r} (use a tônica maior, ex.: G, D, F, Bb, F#)")
    n = _ARMADURAS[armadura]
    if n >= 0:
        return {letra: "#" for letra in _ORDEM_SUSTENIDOS[:n]}
    return {letra: "b" for letra in _ORDEM_BEMOIS[:-n]}


def _nota_abc(
    nota: str, estado_compasso: dict[tuple[str, int], str], da_armadura: dict[str, str] | None = None
) -> str:
    letra, acidente, oitava = _partes(nota)
    chave = (letra, oitava)
    da_armadura = da_armadura or {}
    atual = estado_compasso.get(chave, da_armadura.get(letra, ""))
    if acidente == atual and chave not in estado_compasso:
        # A armadura (ou a ausência dela) já dá o acidente certo.
        prefixo = ""
    elif acidente == atual:
        # Acidente já vale no compasso; repete por clareza quando houver acidente.
        prefixo = _ACIDENTES_ABC[acidente]
    elif acidente == "":
        prefixo = "="
    else:
        prefixo = _ACIDENTES_ABC[acidente]
    estado_compasso[chave] = acidente
    if oitava >= 5:
        corpo = letra.lower() + "'" * (oitava - 5)
    else:
        corpo = letra + "," * (4 - oitava)
    return prefixo + corpo


def eventos_para_abc(
    eventos: list[dict],
    compasso: str = "4/4",
    anacruse: float = 0,
    clave: str = "sol",
    titulo: str | None = None,
    andamento: int | None = None,
    armadura: str = "C",
) -> str:
    """Converte eventos {"notas": [...], "duracao": tempos} em ABC.

    Uma lista vazia de notas é pausa; várias notas formam um acorde (intervalo harmônico).
    Eventos com "silaba" geram a linha de letra (w:) sob as notas.
    Barras de compasso são inseridas automaticamente; uma nota que atravessa a barra
    é aceita só quando cabe no compasso (não fazemos ligaduras automáticas).
    """
    m = re.match(r"^(\d+)/(\d+)$", compasso)
    if not m:
        raise ErroTeoria(f"fórmula de compasso inválida: {compasso!r}")
    num, den = int(m.group(1)), int(m.group(2))
    tempos_por_compasso = Fraction(num * 4, den)

    linhas = ["X:1"]
    if titulo:
        linhas.append(f"T:{titulo}")
    linhas += [f"M:{compasso}", "L:1/4"]
    if andamento:
        linhas.append(f"Q:1/4={andamento}")
    da_armadura = acidentes_da_armadura(armadura)
    linhas.append(f"K:{armadura} clef=bass" if clave == "fa" else f"K:{armadura}")

    corpo: list[str] = []
    estado: dict[tuple[str, int], str] = {}
    restante = Fraction(anacruse).limit_denominator(64) if anacruse else tempos_por_compasso
    forquilha_aberta = None
    for ev in eventos:
        dur = Fraction(ev["duracao"]).limit_denominator(64)
        if dur > restante:
            raise ErroTeoria(
                f"o evento {ev['notas'] or 'pausa'} ({float(dur)} tempos) atravessa a barra de compasso"
            )
        notas = ev["notas"]
        sufixo = _duracao_abc(dur)
        decoracao = ""
        forquilha = ev.get("forquilha")
        if forquilha == "fim":
            if forquilha_aberta is None:
                raise ErroTeoria("forquilha encerrada sem ter começado")
            decoracao += "!<)!" if forquilha_aberta == "crescendo" else "!>)!"
            forquilha_aberta = None
        decoracao += (f"!{ev['dinamica']}!" if ev.get("dinamica") else "") + ("!>!" if ev.get("acento") else "")
        if forquilha in ("crescendo", "diminuendo"):
            if forquilha_aberta is not None:
                raise ErroTeoria("uma forquilha começou antes de a anterior terminar")
            decoracao += "!<(!" if forquilha == "crescendo" else "!>(!"
            forquilha_aberta = forquilha
        if ev.get("staccato") and notas:
            decoracao += "."
        abre = "(" if ev.get("expressao") == "inicio" else ""
        fecha = ")" if ev.get("expressao") == "fim" else ""
        liga = "-" if ev.get("ligada") and notas else ""
        if not notas:
            corpo.append(decoracao + "z" + sufixo)
        elif len(notas) == 1:
            corpo.append(abre + decoracao + _nota_abc(notas[0], estado, da_armadura) + sufixo + liga + fecha)
        else:
            corpo.append(abre + decoracao + "[" + "".join(_nota_abc(n, estado, da_armadura) for n in notas) + "]" + sufixo + liga + fecha)
        restante -= dur
        if restante == 0:
            corpo.append("|")
            estado = {}
            restante = tempos_por_compasso
    if forquilha_aberta is not None:
        raise ErroTeoria("forquilha sem fim: marque forquilha=\"fim\" na nota de chegada")
    if corpo and corpo[-1] == "|":
        corpo[-1] = "|]"
    else:
        corpo.append("|]")
    abc = "\n".join(linhas) + "\n" + " ".join(corpo) + "\n"
    letra = _letra_abc(eventos)
    if letra:
        abc += f"w:{letra}\n"
    return abc


def _letra_abc(eventos: list[dict]) -> str:
    """Linha w: do ABC: uma sílaba por nota (pausas não levam sílaba); "*" pula a nota e "~" junta duas palavras na mesma nota."""
    if not any(ev.get("silaba") for ev in eventos):
        return ""
    letra = ""
    for ev in eventos:
        if not ev["notas"]:
            continue
        silaba = re.sub(r"[\s_*|\\]", "", ev.get("silaba") or "") or "*"
        letra += silaba if silaba.endswith("-") else silaba + " "
    return letra.strip()


def alturas_do_abc(abc: str) -> list[list[int]]:
    """Lê ABC com music21 e devolve as alturas MIDI de cada evento (pausa = [])."""
    # No ABC a clave só muda o desenho; as letras continuam com a altura absoluta. O music21 desloca as notas
    # duas oitavas quando lê "clef=bass", então a clave sai antes da leitura.
    s = converter.parse(abc.replace(" clef=bass", ""), format="abc")
    resultado = []
    for el in s.flatten().notesAndRests:
        if el.isRest:
            resultado.append([])
        else:
            resultado.append(sorted(int(p.midi) for p in el.pitches))
    return resultado
