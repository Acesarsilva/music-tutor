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


def renderizar(aula: Aula, timbre: str = "piano", fragmento: bool = False) -> str:
    """Valida e renderiza. `fragmento=True` omite doctype/html/head/body (para embutir)."""
    if timbre not in TIMBRES:
        raise ValueError(f"timbre deve ser um de {TIMBRES}")
    resultado: Resultado = validar_aula(aula)
    if not resultado.ok:
        raise AulaInvalida(resultado.erros)

    teclados = {}
    for i, secao in enumerate(aula.secoes):
        for j, bloco in enumerate(secao.blocos):
            if bloco.tipo == "teclado":
                teclados[f"t-{i}-{j}"] = _teclado(bloco.de, bloco.ate, bloco.destaque)
    for exe in resultado.exercicios:
        if exe["tipo"] == "teclado":
            original = aula.exercicios[exe["indice"]]
            exe["teclado"] = _teclado(original.de, original.ate, [original.nota_base])

    dados = {
        "codigo": aula.codigo,
        "preferencias": {"timbre": timbre},
        "exemplos": resultado.exemplos,
        "teclados": teclados,
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
        nivel_pt={"iniciante": "Iniciante", "intermediario": "Intermediário", "avancado": "Avançado"}[aula.nivel],
    )
