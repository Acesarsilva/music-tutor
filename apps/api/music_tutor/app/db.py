"""Acesso ao Postgres do Supabase com o RLS valendo para o aluno logado.

Cada requisição abre uma transação, assume o papel `authenticated` e grava as claims do token em
`request.jwt.claims`, do mesmo jeito que o Supabase faz. Assim `auth.uid()` e as políticas de RLS
valem também aqui: um erro na API não expõe dados de outro aluno.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import Depends
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .auth import Usuario, usuario_logado
from .config import config

_pool: ConnectionPool | None = None


def pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        url = config().database_url
        if not url:
            raise RuntimeError("defina DATABASE_URL")
        # prepare_threshold=None: o pooler do Supabase (modo transação) não aceita prepared statements.
        _pool = ConnectionPool(
            url, min_size=1, max_size=10, open=True,
            kwargs={"row_factory": dict_row, "prepare_threshold": None},
        )
    return _pool


def fechar() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def como_usuario(usuario: Usuario) -> Iterator[Connection]:
    with pool().connection() as conn, conn.transaction():
        conn.execute("set local role authenticated")
        conn.execute("select set_config('request.jwt.claims', %s, true)", (json.dumps(usuario.claims),))
        yield conn


def conexao(usuario: Usuario = Depends(usuario_logado)) -> Iterator[Connection]:
    with como_usuario(usuario) as conn:
        yield conn
