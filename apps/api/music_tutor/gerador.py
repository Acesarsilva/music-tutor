"""Gera uma aula com a Claude API e repete a geração até ela passar na validação."""

from __future__ import annotations

import json
import os
from pathlib import Path

import anthropic
import yaml

from .esquema import Aula
from .validacao import validar_aula

RAIZ_REPO = Path(__file__).resolve().parents[3]
PASTA_CURRICULO = RAIZ_REPO / "curriculo"
AULA_REFERENCIA = RAIZ_REPO / "aulas-exemplo" / "I08-intervalos-simples.json"

MODELO_PADRAO = "claude-opus-5-5"
TENTATIVAS_DE_CORRECAO = 2

INSTRUCOES = """\
Você é o professor de teoria musical do app music-tutor e escreve aulas para alunos brasileiros.

Como escrever:
- Português do Brasil, frases curtas e diretas, tom de professor paciente. Sem emojis.
- Nomes de notas em dó-ré-mi no texto (Dó, Ré, Mi, Fá♯, Si♭). Cifras (C, Dm, G7) só para acordes.
- Nos campos de notas dos exemplos use notação científica ASCII: "C4", "F#4", "Bb3". Dó4 é o Dó central.
- Cada conceito novo vem com um exemplo sonoro curto. Prefira exemplos de 1 a 4 compassos.
- Repertório variado (MPB, pop, jazz, erudito, folclore). Exemplos tocados devem usar só melodias em
  domínio público ou trechos curtos de poucas notas; em tabelas, cite a música e o trecho.
- Não invente fatos. Se não tiver certeza de que uma música começa com certo intervalo, não a cite.
- Respeite o escopo do módulo: o que estiver em "fora_do_escopo" pode ser só mencionado.

Formato:
- Responda apenas com o JSON da aula, no esquema fornecido.
- Sempre que um exemplo ou exercício afirmar um intervalo, preencha o campo "intervalo" com as notas e o
  código (número + J/M/m/A/d, por exemplo "3M", "5J", "2m"). Ele será conferido com music21.
- Em perguntas de múltipla escolha sobre um intervalo mostrado, a opção correta deve ser exatamente o nome
  do intervalo, como "3ª menor" ou "5ª justa".
- Exercícios de percepção precisam do campo "intervalo" no exemplo.
- Inclua de 8 a 14 exercícios misturando os tipos pedidos no módulo.
- Ajuste a aula ao perfil do aluno: reforce os pontos fracos e use o timbre preferido nos comentários.
"""


def carregar_modulo(codigo: str) -> dict:
    encontrados = sorted(PASTA_CURRICULO.glob(f"**/{codigo}-*.yaml"))
    if not encontrados:
        raise FileNotFoundError(f"módulo {codigo} não encontrado em {PASTA_CURRICULO}")
    return yaml.safe_load(encontrados[0].read_text(encoding="utf-8"))


def _mensagem_inicial(modulo: dict, perfil: dict, referencia: str | None) -> str:
    partes = [
        "Escreva a aula deste módulo do currículo.",
        "<modulo>\n" + yaml.safe_dump(modulo, allow_unicode=True, sort_keys=False) + "</modulo>",
        "<perfil_do_aluno>\n" + json.dumps(perfil, ensure_ascii=False, indent=2) + "\n</perfil_do_aluno>",
    ]
    if referencia:
        partes.append(
            "Esta é uma aula aprovada de outro módulo. Use-a como referência de tom, profundidade e formato, "
            "não como conteúdo:\n<aula_referencia>\n" + referencia + "\n</aula_referencia>"
        )
    return "\n\n".join(partes)


def gerar_aula(
    codigo: str,
    perfil: dict | None = None,
    cliente: anthropic.Anthropic | None = None,
    modelo: str | None = None,
) -> Aula:
    """Pede a aula ao Claude, valida com music21 e devolve os erros para correção, se houver."""
    cliente = cliente or anthropic.Anthropic()
    modelo = modelo or os.environ.get("MUSIC_TUTOR_MODELO", MODELO_PADRAO)
    modulo = carregar_modulo(codigo)
    perfil = perfil or {"nivel": modulo.get("nivel", "iniciante"), "timbre": "piano", "pontos_fracos": []}
    referencia = None
    if AULA_REFERENCIA.exists() and modulo.get("codigo") != "I08":
        referencia = AULA_REFERENCIA.read_text(encoding="utf-8")

    mensagens: list[dict] = [{"role": "user", "content": _mensagem_inicial(modulo, perfil, referencia)}]
    ultimo_erro: list[str] = []
    for _ in range(TENTATIVAS_DE_CORRECAO + 1):
        with cliente.beta.messages.stream(
            model=modelo,
            max_tokens=64000,
            system=[{"type": "text", "text": INSTRUCOES, "cache_control": {"type": "ephemeral"}}],
            messages=mensagens,
            output_config={"effort": "high"},
            output_format=Aula,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            resposta = stream.get_final_message()

        if resposta.stop_reason == "refusal":
            raise RuntimeError("o modelo recusou gerar esta aula")
        if resposta.stop_reason == "max_tokens":
            raise RuntimeError("a aula ficou longa demais e foi cortada; reduza o escopo do módulo")

        aula = resposta.parsed_output
        resultado = validar_aula(aula)
        if resultado.ok:
            return aula

        ultimo_erro = resultado.erros
        mensagens.append({"role": "assistant", "content": resposta.content})
        mensagens.append(
            {
                "role": "user",
                "content": "A validação com music21 encontrou estes problemas. Corrija e devolva a aula "
                "inteira de novo:\n- " + "\n- ".join(resultado.erros),
            }
        )

    raise RuntimeError("a aula não passou na validação depois das correções:\n- " + "\n- ".join(ultimo_erro))
