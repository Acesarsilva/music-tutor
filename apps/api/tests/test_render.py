import json
import re

import pytest

from music_tutor.render import AulaInvalida, renderizar


def _dados(html: str) -> dict:
    bruto = re.search(r'<script type="application/json" id="dados-aula">(.*?)</script>', html, re.S).group(1)
    return json.loads(bruto.replace("<\\/", "</"))


def test_render_completo(aula_piloto):
    html = renderizar(aula_piloto, timbre="violao")
    assert html.lstrip().startswith("<!doctype html>")
    dados = _dados(html)
    assert dados["preferencias"]["timbre"] == "violao"
    assert "ex-parabens" in dados["exemplos"]
    assert html.count('class="exercicio"') == len(aula_piloto.exercicios)


def test_fragmento_sem_esqueleto(aula_piloto):
    html = renderizar(aula_piloto, fragmento=True)
    assert "<html" not in html and "<body" not in html
    assert "<title>Intervalos simples</title>" in html


def test_html_do_modelo_e_escapado(aula_piloto):
    aula_piloto.secoes[0].blocos[0].markdown = "Texto <script>alert(1)</script> **ok**"
    aula_piloto.secoes[0].titulo = "</script><script>alert(2)</script>"
    html = renderizar(aula_piloto)
    assert "<script>alert(1)</script>" not in html
    assert "<script>alert(2)</script>" not in html
    assert "<strong>ok</strong>" in html


def test_aula_invalida_nao_renderiza(aula_piloto):
    aula_piloto.exercicios[1].correta = 0
    with pytest.raises(AulaInvalida):
        renderizar(aula_piloto)
