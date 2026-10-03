"""Testes da API e do RLS num Postgres de verdade, com o mínimo do Supabase simulado.

Precisam de TEST_DATABASE_URL apontando para um Postgres onde o usuário pode criar bancos, por exemplo
postgresql://postgres@localhost:5432/postgres. Sem a variável, os testes são pulados.
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import date, timedelta

import jwt
import psycopg
import pytest
from psycopg.rows import dict_row

from conftest import RAIZ, escolha_sobre_intervalo, teclado_re_quinta

URL_BASE = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL_BASE, reason="defina TEST_DATABASE_URL para testar a API com Postgres")

SEGREDO = "segredo-de-teste-com-pelo-menos-32-bytes!"
BANCO = "music_tutor_teste"


def _url_do_banco(nome: str) -> str:
    base = psycopg.conninfo.conninfo_to_dict(URL_BASE)
    base["dbname"] = nome
    return psycopg.conninfo.make_conninfo(**base)


@pytest.fixture(scope="module")
def banco():
    with psycopg.connect(URL_BASE, autocommit=True) as admin:
        admin.execute(f"drop database if exists {BANCO} with (force)")
        admin.execute(f"create database {BANCO}")
    url = _url_do_banco(BANCO)
    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute((RAIZ / "supabase" / "testes" / "supabase_simulado.sql").read_text(encoding="utf-8"))
        for migracao in sorted((RAIZ / "supabase" / "migrations").glob("*.sql")):
            conn.execute(migracao.read_text(encoding="utf-8"))
        from music_tutor.app.curriculo import ler_modulos, sincronizar

        sincronizar(conn, ler_modulos())
    yield url


@pytest.fixture(scope="module")
def cliente(banco):
    from fastapi.testclient import TestClient

    os.environ.update(DATABASE_URL=banco, SUPABASE_JWT_SECRET=SEGREDO, SUPABASE_URL="", SUPABASE_SERVICE_ROLE_KEY="")
    from music_tutor.app import config as cfg
    from music_tutor.app import db

    cfg.config.cache_clear()
    db.fechar()
    from music_tutor.app.main import app

    with TestClient(app) as c:
        yield c
    db.fechar()


def criar_usuario(banco: str, nome: str = "Aluno", admin: bool = False) -> tuple[str, str]:
    uid, email = str(uuid.uuid4()), f"{uuid.uuid4().hex[:8]}@exemplo.com"
    with psycopg.connect(banco, autocommit=True) as conn:
        conn.execute(
            "insert into auth.users (id, email, raw_user_meta_data) values (%s, %s, %s::jsonb)",
            (uid, email, f'{{"nome": "{nome}"}}'),
        )
        if admin:
            conn.execute("update public.profiles set papel = 'admin' where id = %s", (uid,))
    return uid, email


def token(uid: str, email: str = "", role: str = "authenticated", exp: int | None = None) -> dict:
    claims = {"sub": uid, "email": email, "role": role, "aud": "authenticated", "exp": exp or int(time.time()) + 3600}
    return {"Authorization": f"Bearer {jwt.encode(claims, SEGREDO, algorithm='HS256')}"}


@pytest.fixture
def aluno(banco):
    uid, email = criar_usuario(banco, "Ana")
    return uid, token(uid, email)


# ------------------------------------------------------------------ Login


def test_sem_token_ou_token_ruim_da_401(cliente, aluno):
    assert cliente.get("/eu").status_code == 401
    assert cliente.get("/eu", headers={"Authorization": "Bearer lixo"}).status_code == 401
    uid, _ = aluno
    assert cliente.get("/eu", headers=token(uid, exp=int(time.time()) - 10)).status_code == 401
    assert cliente.get("/eu", headers=token(uid, role="anon")).status_code == 401


def test_perfil_criado_no_convite_e_editado(cliente, aluno):
    _, h = aluno
    perfil = cliente.get("/eu", headers=h).json()
    assert perfil["nome"] == "Ana" and perfil["papel"] == "aluno" and perfil["timbre"] == "piano"
    assert perfil["termos_aceitos_em"] is None

    perfil = cliente.patch("/eu", headers=h, json={"timbre": "violao", "aceitar_termos": True}).json()
    assert perfil["timbre"] == "violao" and perfil["termos_aceitos_em"] is not None
    assert cliente.patch("/eu", headers=h, json={"timbre": "flauta"}).status_code == 422


# ------------------------------------------------------------------ Aulas e progresso


def test_painel_mostra_o_curriculo(cliente, aluno):
    _, h = aluno
    painel = cliente.get("/painel", headers=h).json()
    i08 = next(m for m in painel["modulos"] if m["codigo"] == "I08")
    assert i08["aula_disponivel"] and i08["status"] is None and i08["dominio"] == 0
    assert painel["revisoes"] == [] and painel["conceitos_fracos"] == []


def test_abrir_aula_no_timbre_do_perfil(cliente, aluno):
    _, h = aluno
    cliente.patch("/eu", headers=h, json={"timbre": "violao"})
    r = cliente.get("/aulas/I08", headers=h)
    assert r.status_code == 200 and "<html" in r.text
    assert '"timbre": "violao"' in r.text
    assert '"timbre": "piano"' in cliente.get("/aulas/I08?timbre=piano", headers=h).text
    i08 = next(m for m in cliente.get("/painel", headers=h).json()["modulos"] if m["codigo"] == "I08")
    assert i08["status"] == "em_andamento"
    assert cliente.get("/aulas/X99", headers=h).status_code == 404


def test_respostas_corrigidas_no_servidor_e_revisao_espacada(cliente, aluno, aula_piloto):
    _, h = aluno
    indice, exe = next((i, e) for i, e in enumerate(aula_piloto.exercicios) if e is escolha_sobre_intervalo(aula_piloto))
    errada = (exe.correta + 1) % len(exe.opcoes)
    hoje = date.today()

    r = cliente.post("/aulas/I08/respostas", headers=h, json={"indice": indice, "opcao": exe.correta}).json()
    assert r == {"certo": True, "conceito": exe.conceito, "dominio": 35, "proxima_revisao": str(hoje + timedelta(days=1))}
    r = cliente.post("/aulas/I08/respostas", headers=h, json={"indice": indice, "opcao": exe.correta}).json()
    assert r["dominio"] == 58 and r["proxima_revisao"] == str(hoje + timedelta(days=3))
    r = cliente.post("/aulas/I08/respostas", headers=h, json={"indice": indice, "opcao": exe.correta}).json()
    assert r["proxima_revisao"] == str(hoje + timedelta(days=7))
    r = cliente.post("/aulas/I08/respostas", headers=h, json={"indice": indice, "opcao": errada}).json()
    assert r["certo"] is False and r["proxima_revisao"] == str(hoje + timedelta(days=1))

    painel = cliente.get("/painel", headers=h).json()
    assert painel["conceitos_fracos"][0]["conceito"] == exe.conceito
    assert painel["conceitos_fracos"][0]["acertos"] == 3 and painel["conceitos_fracos"][0]["erros"] == 1
    i08 = next(m for m in painel["modulos"] if m["codigo"] == "I08")
    assert 0 < i08["dominio"] < 100


def test_resposta_de_teclado_e_respostas_invalidas(cliente, aluno, aula_piloto):
    from music_tutor import teoria

    _, h = aluno
    exe = teclado_re_quinta(aula_piloto)
    indice = aula_piloto.exercicios.index(exe)
    alvo = teoria.midi("A4")
    assert cliente.post("/aulas/I08/respostas", headers=h, json={"indice": indice, "midi": alvo}).json()["certo"] is True
    assert cliente.post("/aulas/I08/respostas", headers=h, json={"indice": indice, "midi": alvo + 1}).json()["certo"] is False
    assert cliente.post("/aulas/I08/respostas", headers=h, json={"indice": indice}).status_code == 422
    assert cliente.post("/aulas/I08/respostas", headers=h, json={"indice": 999, "opcao": 0}).status_code == 404


def test_concluir_modulo_agenda_revisao(cliente, aluno):
    _, h = aluno
    r = cliente.post("/aulas/I08/concluir", headers=h).json()
    assert r["status"] == "concluido" and r["proxima_revisao"] == str(date.today() + timedelta(days=1))
    assert cliente.post("/aulas/X99/concluir", headers=h).status_code == 404


# ------------------------------------------------------------------ Isolamento entre alunos (RLS)


def _como(banco: str, uid: str | None):
    conn = psycopg.connect(banco, row_factory=dict_row)
    papel = "authenticated" if uid else "anon"
    conn.execute(f"set role {papel}")
    if uid:
        conn.execute("select set_config('request.jwt.claims', %s, false)", (f'{{"sub": "{uid}", "role": "authenticated"}}',))
    return conn


def test_rls_isola_os_alunos(cliente, banco):
    a, _ = criar_usuario(banco, "A")
    b, email_b = criar_usuario(banco, "B")
    hb = token(b, email_b)
    cliente.post("/aulas/I08/concluir", headers=hb)
    cliente.post("/aulas/I08/respostas", headers=hb, json={"indice": 0, "opcao": 0})

    with _como(banco, a) as conn:
        assert [p["id"] for p in conn.execute("select id from profiles").fetchall()] == [uuid.UUID(a)]
        for tabela in ("module_progress", "concept_mastery", "quiz_attempts"):
            assert conn.execute(f"select count(*) as n from {tabela}").fetchone()["n"] == 0
        assert conn.execute("update profiles set nome = 'x' where id = %s", (b,)).rowcount == 0
        assert conn.execute("select count(*) as n from modules").fetchone()["n"] >= 1

    with _como(banco, b) as conn:
        assert conn.execute("select count(*) as n from quiz_attempts").fetchone()["n"] == 1


@pytest.mark.parametrize(
    "comando",
    [
        "update profiles set papel = 'admin' where id = auth.uid()",
        "insert into concept_mastery (user_id, conceito, dominio) values (auth.uid(), 'x', 100)",
        "update module_progress set dominio = 100",
        "insert into modules (codigo, titulo, nivel) values ('Z01', 'z', 'iniciante')",
        "delete from quiz_attempts",
    ],
)
def test_aluno_nao_grava_direto(banco, comando):
    uid, _ = criar_usuario(banco)
    with _como(banco, uid) as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute(comando)


def test_visitante_sem_login_nao_le_nada(banco):
    criar_usuario(banco)
    with _como(banco, None) as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute("select * from profiles")
    with _como(banco, None) as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute("select registrar_resposta('x', true)")


def test_cota_diaria(banco):
    uid, _ = criar_usuario(banco)
    with _como(banco, uid) as conn:
        resultados = [conn.execute("select consumir_cota('aulas', 2) as ok").fetchone()["ok"] for _ in range(3)]
    assert resultados == [True, True, False]


# ------------------------------------------------------------------ Administração e LGPD


def test_so_admin_convida_e_lista(cliente, banco, aluno, monkeypatch):
    from music_tutor.app import supabase_admin

    _, h = aluno
    assert cliente.post("/admin/convites", headers=h, json={"email": "novo@exemplo.com"}).status_code == 403
    assert cliente.get("/admin/alunos", headers=h).status_code == 403

    admin_id, admin_email = criar_usuario(banco, "César", admin=True)
    ha = token(admin_id, admin_email)
    # Sem a chave do Supabase configurada, o convite avisa em vez de falhar em silêncio.
    assert cliente.post("/admin/convites", headers=ha, json={"email": "novo@exemplo.com"}).status_code == 503

    enviados = []
    monkeypatch.setattr(supabase_admin, "convidar", lambda cfg, email, nome: enviados.append((email, nome)) or {"id": "x"})
    r = cliente.post("/admin/convites", headers=ha, json={"email": "novo@exemplo.com", "nome": "Bia"})
    assert r.status_code == 201 and enviados == [("novo@exemplo.com", "Bia")]
    assert cliente.post("/admin/convites", headers=ha, json={"email": "não é e-mail"}).status_code == 422

    alunos = cliente.get("/admin/alunos", headers=ha).json()
    assert {"Ana", "César"} <= {a["nome"] for a in alunos}


def test_exportar_e_excluir_conta(cliente, banco, aluno, monkeypatch):
    from music_tutor.app import supabase_admin

    uid, h = aluno
    cliente.post("/aulas/I08/respostas", headers=h, json={"indice": 0, "opcao": 0})
    dados = cliente.get("/eu/dados", headers=h).json()
    assert dados["perfil"]["nome"] == "Ana" and len(dados["quiz_attempts"]) == 1

    assert cliente.request("DELETE", "/eu", headers=h, json={"confirmo": "sim"}).status_code == 422
    excluidos = []

    def excluir(cfg, user_id):
        excluidos.append(user_id)
        with psycopg.connect(banco, autocommit=True) as conn:
            conn.execute("delete from auth.users where id = %s", (user_id,))

    monkeypatch.setattr(supabase_admin, "excluir_usuario", excluir)
    assert cliente.request("DELETE", "/eu", headers=h, json={"confirmo": "EXCLUIR"}).status_code == 204
    assert excluidos == [uid]
    with psycopg.connect(banco) as conn:
        assert conn.execute("select count(*) from quiz_attempts where user_id = %s", (uid,)).fetchone()[0] == 0
