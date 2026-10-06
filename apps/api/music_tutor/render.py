"""Monta o HTML de uma aula a partir do JSON validado e do template."""

from __future__ import annotations

import html
import json
from pathlib import Path

import markdown as md
from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import teoria
from .esquema import Aula
from .validacao import Resultado, validar_aula

RAIZ_REPO = Path(__file__).resolve().parents[3]
PASTA_TEMPLATES = RAIZ_REPO / "templates-aula"

TIMBRES = ("piano", "violao")


class AulaInvalida(ValueError):
    def __init__(self, erros: list[str]):
        super().__init__("a aula não passou na validação:\n- " + "\n- ".join(erros))
        self.erros = erros


def _markdown(texto: str) -> str:
    # O texto vem do modelo: escapamos HTML antes de converter o markdown.
    return md.markdown(html.escape(texto, quote=False), extensions=["sane_lists"])


def _markdown_linha(texto: str) -> str:
    convertido = _markdown(texto).strip()
    if convertido.startswith("<p>") and convertido.endswith("</p>") and convertido.count("<p>") == 1:
        return convertido[3:-4]
    return convertido


def _json_seguro(dados: dict) -> str:
    return json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")


def _teclado(de: str, ate: str, destaque: list[str]) -> dict:
    return {
        "de": teoria.midi(de),
        "ate": teoria.midi(ate),
        "destaque": [{"midi": teoria.midi(n), "nome": teoria.nome_nota_pt(n)} for n in destaque],
    }


def _diagrama_acorde(cifra: str, casas: list[int], dedos: list[int], pestana: int | None) -> str:
    """SVG do diagrama de acorde: cordas na vertical (6ª à esquerda), trastes na horizontal, pestana no topo."""
    presas = [c for c in casas if c > 0]
    inicio = 1 if not presas or max(presas) <= 5 else min(presas)
    trastes = max(5, (max(presas) - inicio + 1) if presas else 5)
    x0, y0, dx, dy = 22, 40, 18, 22
    largura, altura = x0 + 5 * dx + 22, y0 + trastes * dy + 14
    p = [f'<svg class="diagrama" viewBox="0 0 {largura} {altura}" width="{largura}" height="{altura}" role="img" '
         f'aria-label="Diagrama do acorde {html.escape(cifra)}">',
         f'<text class="diagrama-cifra" x="{x0 + 2.5 * dx}" y="16" text-anchor="middle">{html.escape(cifra)}</text>']
    for k in range(6):
        x = x0 + k * dx
        p.append(f'<line class="diagrama-corda" x1="{x}" y1="{y0}" x2="{x}" y2="{y0 + trastes * dy}"/>')
    for t in range(trastes + 1):
        y = y0 + t * dy
        classe = "diagrama-pestana-fixa" if t == 0 and inicio == 1 else "diagrama-traste"
        p.append(f'<line class="{classe}" x1="{x0}" y1="{y}" x2="{x0 + 5 * dx}" y2="{y}"/>')
    if inicio > 1:
        p.append(f'<text class="diagrama-casa" x="{x0 - 7}" y="{y0 + dy / 2 + 4}" text-anchor="end">{inicio}</text>')
    if pestana is not None:
        cordas = [k for k, c in enumerate(casas) if c == pestana]
        y = y0 + (pestana - inicio + 0.5) * dy
        xa, xb = x0 + cordas[0] * dx, x0 + 5 * dx
        p.append(f'<rect class="diagrama-dedo" x="{xa - 7}" y="{y - 7}" width="{xb - xa + 14}" height="14" rx="7"/>')
        p.append(f'<text class="diagrama-numero" x="{xa}" y="{y + 4}" text-anchor="middle">1</text>')
    for k, casa in enumerate(casas):
        x = x0 + k * dx
        if casa == -1:
            p.append(f'<text class="diagrama-marca" x="{x}" y="{y0 - 8}" text-anchor="middle">×</text>')
        elif casa == 0:
            p.append(f'<circle class="diagrama-solta" cx="{x}" cy="{y0 - 12}" r="4.5"/>')
        elif not (pestana is not None and casa == pestana):
            y = y0 + (casa - inicio + 0.5) * dy
            p.append(f'<circle class="diagrama-dedo" cx="{x}" cy="{y}" r="7.5"/>')
            if dedos and dedos[k]:
                p.append(f'<text class="diagrama-numero" x="{x}" y="{y + 4}" text-anchor="middle">{dedos[k]}</text>')
    p.append("</svg>")
    return "".join(p)


def renderizar(aula: Aula, timbre: str | None = None, fragmento: bool = False, voltar: str | None = None) -> str:
    """Valida e renderiza. `fragmento=True` omite doctype/html/head/body (para embutir).
    `voltar` é o endereço da lista de aulas, mostrado como link na barra (usado no site).
    Sem `timbre`, as aulas de violão abrem com o violão e as outras com o piano."""
    if timbre is None:
        timbre = "violao" if aula.assunto == "violao" else "piano"
    if timbre not in TIMBRES:
        raise ValueError(f"timbre deve ser um de {TIMBRES}")
    resultado: Resultado = validar_aula(aula)
    if not resultado.ok:
        raise AulaInvalida(resultado.erros)

    teclados, acordes, diagramas = {}, {}, {}
    for i, secao in enumerate(aula.secoes):
        for j, bloco in enumerate(secao.blocos):
            if bloco.tipo == "teclado":
                teclados[f"t-{i}-{j}"] = _teclado(bloco.de, bloco.ate, bloco.destaque)
            elif bloco.tipo == "acorde":
                acordes[f"a-{i}-{j}"] = [teoria.midi(n) for n in teoria.notas_do_violao(bloco.casas)]
                diagramas[f"a-{i}-{j}"] = _diagrama_acorde(bloco.cifra, bloco.casas, bloco.dedos, bloco.pestana)
    for exe in resultado.exercicios:
        if exe["tipo"] == "teclado":
            original = aula.exercicios[exe["indice"]]
            exe["teclado"] = _teclado(original.de, original.ate, [original.nota_base])

    dados = {
        "codigo": aula.codigo,
        "preferencias": {"timbre": timbre},
        "exemplos": resultado.exemplos,
        "teclados": teclados,
        "acordes": acordes,
        "exercicios": resultado.exercicios,
    }

    env = Environment(
        loader=FileSystemLoader(PASTA_TEMPLATES),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["md"] = _markdown
    env.filters["md_linha"] = _markdown_linha
    template = env.get_template("aula.html.j2")
    return template.render(
        aula=aula,
        dados_json=_json_seguro(dados),
        css=(PASTA_TEMPLATES / "aula.css").read_text(encoding="utf-8"),
        js=(PASTA_TEMPLATES / "aula.js").read_text(encoding="utf-8"),
        fragmento=fragmento,
        timbre=timbre,
        voltar=voltar,
        diagramas=diagramas,
        assunto_pt={"teoria": "Teoria musical", "violao": "Violão"}[aula.assunto],
        nivel_pt={"iniciante": "Iniciante", "intermediario": "Intermediário", "avancado": "Avançado"}[aula.nivel],
    )
