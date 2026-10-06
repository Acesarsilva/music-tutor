"""Gera o site estático com as aulas prontas: uma página de índice por nível e uma página por aula.

    python -m music_tutor site -o dist

Entra no site toda aula com JSON em aulas-exemplo/ cujo módulo existe em curriculo/.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .esquema import Aula
from .render import PASTA_TEMPLATES, RAIZ_REPO, _markdown_linha, renderizar

PASTA_AULAS = RAIZ_REPO / "aulas-exemplo"
PASTA_CURRICULO = RAIZ_REPO / "curriculo"

NIVEIS = {"iniciante": "Iniciante", "intermediario": "Intermediário", "avancado": "Avançado"}
ASSUNTOS = {"teoria": "Teoria", "violao": "Violão"}
# Teoria usa I, M e A; violão, VI, VM e VA.
_BASE_ORDEM = {"I": 0, "M": 100, "A": 200, "VI": 1000, "VM": 1100, "VA": 1200}
_CODIGO_RE = re.compile(r"^([A-Z]+)(\d+)$")


def _ordem(codigo: str) -> int:
    achado = _CODIGO_RE.match(codigo)
    if not achado or achado.group(1) not in _BASE_ORDEM:
        return 9999
    return _BASE_ORDEM[achado.group(1)] + int(achado.group(2))


def _modulos(pasta: Path) -> dict[str, dict]:
    modulos = {}
    for arquivo in pasta.rglob("*.yaml"):
        dados = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
        modulos[dados["codigo"]] = dados
    return modulos


def aulas_prontas(pasta_aulas: Path = PASTA_AULAS, pasta_curriculo: Path = PASTA_CURRICULO) -> list[tuple[Aula, str]]:
    """(aula, nome do arquivo HTML), na ordem do currículo."""
    modulos = _modulos(pasta_curriculo)
    aulas = []
    for arquivo in sorted(pasta_aulas.glob("*.json")):
        aula = Aula.model_validate_json(arquivo.read_text(encoding="utf-8"))
        if aula.codigo in modulos:
            aulas.append((aula, f"{arquivo.stem}.html"))
    return sorted(aulas, key=lambda par: _ordem(par[0].codigo))


def gerar_site(saida: Path, pasta_aulas: Path = PASTA_AULAS, pasta_curriculo: Path = PASTA_CURRICULO) -> int:
    if saida.exists():
        shutil.rmtree(saida)
    (saida / "aulas").mkdir(parents=True)

    aulas = aulas_prontas(pasta_aulas, pasta_curriculo)
    for aula, nome in aulas:
        (saida / "aulas" / nome).write_text(renderizar(aula, voltar="../"), encoding="utf-8")

    niveis = []
    for assunto, nome_assunto in ASSUNTOS.items():
        for nivel, rotulo in NIVEIS.items():
            do_nivel = [
                {"codigo": a.codigo, "titulo": a.titulo, "resumo": a.resumo_curto, "href": f"aulas/{nome}"}
                for a, nome in aulas if a.assunto == assunto and a.nivel == nivel
            ]
            if do_nivel:
                niveis.append({"rotulo": f"{nome_assunto} · {rotulo}", "aulas": do_nivel})

    env = Environment(loader=FileSystemLoader(PASTA_TEMPLATES), autoescape=select_autoescape(["html", "j2"]))
    env.filters["md_linha"] = _markdown_linha
    indice = env.get_template("indice.html.j2").render(niveis=niveis, total=len(aulas))
    (saida / "index.html").write_text(indice, encoding="utf-8")
    return len(aulas)
