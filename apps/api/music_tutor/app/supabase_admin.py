"""Chamadas à API de administração do Supabase Auth (convites, lista e exclusão de contas)."""

from __future__ import annotations

import httpx

from .config import Config


class SupabaseIndisponivel(RuntimeError):
    pass


def _cliente(cfg: Config) -> httpx.Client:
    if not (cfg.supabase_url and cfg.supabase_service_key):
        raise SupabaseIndisponivel("defina SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY na API")
    return httpx.Client(
        base_url=f"{cfg.supabase_url.rstrip('/')}/auth/v1",
        headers={"apikey": cfg.supabase_service_key, "Authorization": f"Bearer {cfg.supabase_service_key}"},
        timeout=15,
    )


def convidar(cfg: Config, email: str, nome: str) -> dict:
    """Envia o e-mail de convite; o link leva o aluno à página de criar senha do site."""
    with _cliente(cfg) as c:
        r = c.post(
            "/invite",
            params={"redirect_to": f"{cfg.site_url.rstrip('/')}/definir-senha"},
            json={"email": email, "data": {"nome": nome}},
        )
    r.raise_for_status()
    return r.json()


def listar_usuarios(cfg: Config) -> dict[str, dict]:
    """id -> {email, ultimo_login, confirmado}."""
    usuarios: dict[str, dict] = {}
    with _cliente(cfg) as c:
        pagina = 1
        while True:
            r = c.get("/admin/users", params={"page": pagina, "per_page": 200})
            r.raise_for_status()
            lote = r.json().get("users", [])
            for u in lote:
                usuarios[u["id"]] = {
                    "email": u.get("email"),
                    "ultimo_login": u.get("last_sign_in_at"),
                    "confirmado": bool(u.get("email_confirmed_at") or u.get("confirmed_at")),
                }
            if len(lote) < 200:
                return usuarios
            pagina += 1


def excluir_usuario(cfg: Config, user_id: str) -> None:
    """Apaga a conta no Auth; as linhas do aluno saem junto (on delete cascade)."""
    with _cliente(cfg) as c:
        r = c.delete(f"/admin/users/{user_id}")
    r.raise_for_status()
