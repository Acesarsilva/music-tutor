"""Lê os módulos do currículo (YAML) e copia para a tabela `modules`."""

from __future__ import annotations

from pathlib import Path

import yaml
from psycopg import Connection

from ..gerador import PASTA_CURRICULO

_BASE_ORDEM = {"I": 0, "M": 100, "A": 200}


def ordem(codigo: str) -> int:
    """I01..I16, M01..M18, A01..A17 em sequência: I08 -> 8, M02 -> 102."""
    try:
        return _BASE_ORDEM.get(codigo[0], 900) + int(codigo[1:])
    except ValueError:
        return 999


def ler_modulos(pasta: Path = PASTA_CURRICULO) -> list[dict]:
    modulos = []
    for arquivo in sorted(pasta.rglob("*.yaml")):
        dados = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
        modulos.append({
            "codigo": dados["codigo"],
            "titulo": dados["titulo"],
            "nivel": dados["nivel"],
            "assunto": dados.get("assunto", "teoria"),
            "ordem": ordem(dados["codigo"]),
            "prerequisitos": [str(p) for p in dados.get("prerequisitos") or []],
            "conceitos": list(dados.get("conceitos") or []),
            "objetivos": list(dados.get("objetivos") or []),
        })
    return modulos


def sincronizar(conn: Connection, modulos: list[dict]) -> int:
    """Insere ou atualiza os módulos (rodar como dono do banco, não como aluno)."""
    with conn.cursor() as cur:
        cur.executemany(
            """
            insert into public.modules (codigo, titulo, nivel, assunto, ordem, prerequisitos, conceitos, objetivos)
            values (%(codigo)s, %(titulo)s, %(nivel)s, %(assunto)s, %(ordem)s, %(prerequisitos)s, %(conceitos)s, %(objetivos)s)
            on conflict (codigo) do update set
              titulo = excluded.titulo, nivel = excluded.nivel, assunto = excluded.assunto, ordem = excluded.ordem,
              prerequisitos = excluded.prerequisitos, conceitos = excluded.conceitos, objetivos = excluded.objetivos,
              atualizado_em = now()
            """,
            modulos,
        )
    return len(modulos)
