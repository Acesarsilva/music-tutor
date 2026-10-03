"""Encontra a aula de um módulo, monta o HTML no timbre do aluno e corrige as respostas no servidor."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from psycopg import Connection

from ..esquema import Aula
from ..render import renderizar
from ..validacao import validar_aula


@dataclass(frozen=True)
class AulaPronta:
    aula: Aula
    exercicios: list[dict]  # versão compilada pelo validador: conceito, correta, alvo


@lru_cache(maxsize=64)
def _ler_arquivo(caminho: Path, _mtime: float) -> AulaPronta:
    aula = Aula.model_validate_json(caminho.read_text(encoding="utf-8"))
    return AulaPronta(aula, validar_aula(aula).exercicios)


def codigos_em_arquivo(pasta: Path) -> set[str]:
    return {p.name.split("-", 1)[0] for p in pasta.glob("*.json")}


def buscar(conn: Connection, codigo: str, pasta: Path) -> AulaPronta | None:
    """Prefere a aula gerada para o aluno, depois a camada base do banco, depois os arquivos publicados."""
    linha = conn.execute(
        """
        select conteudo from public.lessons
        where modulo = %s and (user_id = auth.uid() or user_id is null)
        order by user_id is null, criado_em desc
        limit 1
        """,
        (codigo,),
    ).fetchone()
    if linha:
        aula = Aula.model_validate(linha["conteudo"])
        return AulaPronta(aula, validar_aula(aula).exercicios)
    arquivos = sorted(pasta.glob(f"{codigo}-*.json"))
    if not arquivos:
        return None
    return _ler_arquivo(arquivos[0], arquivos[0].stat().st_mtime)


@lru_cache(maxsize=128)
def _html(aula_json: str, timbre: str) -> str:
    return renderizar(Aula.model_validate_json(aula_json), timbre=timbre)


def html(pronta: AulaPronta, timbre: str) -> str:
    return _html(pronta.aula.model_dump_json(), timbre)


def corrigir(pronta: AulaPronta, indice: int, opcao: int | None, midi: int | None) -> tuple[dict, bool, str]:
    """Devolve (exercício compilado, acertou?, resposta em texto). IndexError/ValueError se a resposta não serve."""
    if not 0 <= indice < len(pronta.exercicios):
        raise IndexError(indice)
    exe = pronta.exercicios[indice]
    original = pronta.aula.exercicios[indice]
    if "correta" in exe:
        if opcao is None or not 0 <= opcao < len(original.opcoes):
            raise ValueError("escolha uma das opções")
        return exe, opcao == exe["correta"], original.opcoes[opcao]
    if "alvo" in exe:
        if midi is None:
            raise ValueError("toque uma nota")
        return exe, midi == exe["alvo"], f"midi {midi}"
    raise ValueError("exercício sem correção automática")
