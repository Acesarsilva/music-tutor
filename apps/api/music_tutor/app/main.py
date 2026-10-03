"""Rotas da API. Rode com: uvicorn music_tutor.app.main:app --reload"""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from typing import Literal

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from psycopg import Connection
from pydantic import BaseModel, EmailStr, Field

from . import aulas, db, supabase_admin
from .auth import Usuario, usuario_logado
from .config import config


@asynccontextmanager
async def _ciclo(_app: FastAPI):
    yield
    db.fechar()


app = FastAPI(title="music-tutor API", version="0.2.0", lifespan=_ciclo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config().site_origens,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


# ------------------------------------------------------------------ Modelos

class PerfilEdicao(BaseModel):
    nome: str | None = Field(None, max_length=120)
    timbre: Literal["piano", "violao"] | None = None
    objetivos: list[str] | None = Field(None, max_length=10)
    aceitar_termos: bool | None = None


class Resposta(BaseModel):
    indice: int = Field(ge=0)
    opcao: int | None = Field(None, ge=0)
    midi: int | None = Field(None, ge=0, le=127)


class Convite(BaseModel):
    email: EmailStr
    nome: str = Field("", max_length=120)


class ConfirmarExclusao(BaseModel):
    confirmo: Literal["EXCLUIR"]


# ------------------------------------------------------------------ Auxiliares

def _perfil(conn: Connection) -> dict:
    perfil = conn.execute("select * from public.profiles where id = auth.uid()").fetchone()
    if perfil is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "perfil não encontrado")
    return perfil


def _exigir_admin(conn: Connection) -> None:
    if not conn.execute("select public.is_admin() as ok").fetchone()["ok"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "só o administrador pode fazer isso")


def _modulo_existe(conn: Connection, codigo: str) -> None:
    if not conn.execute("select 1 from public.modules where codigo = %s", (codigo,)).fetchone():
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"módulo {codigo} não existe no currículo")


def _erro_supabase(e: Exception) -> HTTPException:
    if isinstance(e, supabase_admin.SupabaseIndisponivel):
        return HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
    if isinstance(e, httpx.HTTPStatusError):
        try:
            detalhe = e.response.json().get("msg") or e.response.json().get("message") or e.response.text
        except ValueError:
            detalhe = e.response.text
        return HTTPException(status.HTTP_502_BAD_GATEWAY, f"o Supabase recusou: {detalhe}")
    return HTTPException(status.HTTP_502_BAD_GATEWAY, "não foi possível falar com o Supabase")


# ------------------------------------------------------------------ Rotas

@app.get("/saude")
def saude() -> dict:
    return {"ok": True}


@app.get("/eu")
def eu(usuario: Usuario = Depends(usuario_logado), conn: Connection = Depends(db.conexao)) -> dict:
    return {**_perfil(conn), "email": usuario.email}


@app.patch("/eu")
def editar_perfil(edicao: PerfilEdicao, conn: Connection = Depends(db.conexao)) -> dict:
    campos = edicao.model_dump(exclude_none=True, exclude={"aceitar_termos"})
    sets = [f"{k} = %({k})s" for k in campos]
    if edicao.aceitar_termos:
        sets.append("termos_aceitos_em = coalesce(termos_aceitos_em, now())")
    if sets:
        conn.execute(f"update public.profiles set {', '.join(sets)} where id = auth.uid()", campos)
    return _perfil(conn)


@app.get("/painel")
def painel(conn: Connection = Depends(db.conexao)) -> dict:
    """Tudo o que a página inicial do aluno mostra numa chamada só."""
    perfil = _perfil(conn)
    modulos = conn.execute(
        """
        select m.codigo, m.titulo, m.nivel, m.ordem, m.prerequisitos,
               p.status, coalesce(p.dominio, 0) as dominio, p.proxima_revisao
        from public.modules m
        left join public.module_progress p on p.modulo = m.codigo and p.user_id = auth.uid()
        order by m.ordem
        """
    ).fetchall()
    disponiveis = aulas.codigos_em_arquivo(config().pasta_aulas) | {
        r["modulo"] for r in conn.execute(
            "select distinct modulo from public.lessons where modulo is not null"
        ).fetchall()
    }
    for m in modulos:
        m["aula_disponivel"] = m["codigo"] in disponiveis
    revisoes = conn.execute(
        """
        select conceito, dominio, proxima_revisao from public.concept_mastery
        where user_id = auth.uid() and proxima_revisao <= current_date
        order by proxima_revisao, dominio limit 20
        """
    ).fetchall()
    fracos = conn.execute(
        """
        select conceito, dominio, acertos, erros from public.concept_mastery
        where user_id = auth.uid() and dominio < 70 order by dominio, erros desc limit 5
        """
    ).fetchall()
    return {"perfil": perfil, "modulos": modulos, "revisoes": revisoes, "conceitos_fracos": fracos, "hoje": date.today()}


@app.get("/aulas/{codigo}", response_class=HTMLResponse)
def abrir_aula(
    codigo: str,
    timbre: Literal["piano", "violao"] | None = Query(None),
    conn: Connection = Depends(db.conexao),
) -> HTMLResponse:
    _modulo_existe(conn, codigo)
    pronta = aulas.buscar(conn, codigo, config().pasta_aulas)
    if pronta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "esta aula ainda não foi publicada")
    timbre = timbre or _perfil(conn)["timbre"]
    conn.execute("select public.marcar_modulo(%s, false)", (codigo,))
    # O site mostra o HTML num iframe isolado; a aula conversa com ele só por postMessage.
    return HTMLResponse(aulas.html(pronta, timbre), headers={"Cache-Control": "private, no-store"})


@app.post("/aulas/{codigo}/respostas")
def responder(codigo: str, resposta: Resposta, conn: Connection = Depends(db.conexao)) -> dict:
    _modulo_existe(conn, codigo)
    pronta = aulas.buscar(conn, codigo, config().pasta_aulas)
    if pronta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "esta aula ainda não foi publicada")
    try:
        exe, certo, texto = aulas.corrigir(pronta, resposta.indice, resposta.opcao, resposta.midi)
    except IndexError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "exercício não existe nesta aula")
    except ValueError as e:
        raise HTTPException(422, str(e))
    dominio = conn.execute(
        "select * from public.registrar_resposta(%s, %s, %s, 'aula', %s, %s)",
        (exe["conceito"], certo, codigo, pronta.aula.exercicios[resposta.indice].enunciado, texto),
    ).fetchone()
    return {"certo": certo, "conceito": exe["conceito"], "dominio": dominio["dominio"],
            "proxima_revisao": dominio["proxima_revisao"]}


@app.post("/aulas/{codigo}/concluir")
def concluir(codigo: str, conn: Connection = Depends(db.conexao)) -> dict:
    _modulo_existe(conn, codigo)
    return conn.execute("select * from public.marcar_modulo(%s, true)", (codigo,)).fetchone()


# ------------------------------------------------------------------ LGPD

@app.get("/eu/dados")
def exportar_dados(usuario: Usuario = Depends(usuario_logado), conn: Connection = Depends(db.conexao)) -> dict:
    """Tudo o que o app guarda sobre o aluno, para ele baixar."""
    tabelas = ["module_progress", "concept_mastery", "quiz_attempts", "lessons", "conversations",
               "messages", "submissions", "learner_notes", "usage_daily"]
    dados = {"perfil": {**_perfil(conn), "email": usuario.email}}
    for t in tabelas:
        dados[t] = conn.execute(f"select * from public.{t} where user_id = auth.uid()").fetchall()
    return dados


@app.delete("/eu", status_code=status.HTTP_204_NO_CONTENT)
def excluir_conta(_c: ConfirmarExclusao, usuario: Usuario = Depends(usuario_logado)) -> None:
    try:
        supabase_admin.excluir_usuario(config(), usuario.id)
    except (supabase_admin.SupabaseIndisponivel, httpx.HTTPError) as e:
        raise _erro_supabase(e)


# ------------------------------------------------------------------ Administração

@app.post("/admin/convites", status_code=status.HTTP_201_CREATED)
def convidar(convite: Convite, conn: Connection = Depends(db.conexao)) -> dict:
    _exigir_admin(conn)
    try:
        criado = supabase_admin.convidar(config(), convite.email, convite.nome)
    except (supabase_admin.SupabaseIndisponivel, httpx.HTTPError) as e:
        raise _erro_supabase(e)
    return {"id": criado.get("id"), "email": convite.email}


@app.get("/admin/alunos")
def alunos(conn: Connection = Depends(db.conexao)) -> list[dict]:
    _exigir_admin(conn)
    linhas = conn.execute(
        """
        select p.id, p.nome, p.papel, p.nivel, p.timbre, p.criado_em, p.termos_aceitos_em,
               (select count(*) from public.module_progress m where m.user_id = p.id and m.status = 'concluido') as modulos_concluidos,
               (select count(*) from public.quiz_attempts q where q.user_id = p.id) as respostas,
               (select max(q.criado_em) from public.quiz_attempts q where q.user_id = p.id) as ultima_resposta
        from public.profiles p order by p.criado_em
        """
    ).fetchall()
    try:
        contas = supabase_admin.listar_usuarios(config())
    except (supabase_admin.SupabaseIndisponivel, httpx.HTTPError):
        contas = {}
    for linha in linhas:
        linha.update(contas.get(str(linha["id"]), {}))
    return linhas
