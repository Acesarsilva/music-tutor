"""Configuração da API, lida das variáveis de ambiente (veja apps/api/.env.exemplo)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from ..render import RAIZ_REPO


def _lista(valor: str) -> list[str]:
    return [v.strip() for v in valor.split(",") if v.strip()]


@dataclass(frozen=True)
class Config:
    database_url: str
    supabase_url: str = ""
    # Chave secreta do Supabase (service_role): só para convidar e excluir contas. Nunca vai ao navegador.
    supabase_service_key: str = ""
    # Projetos antigos assinam o token com um segredo (HS256); os novos publicam chaves em JWKS.
    supabase_jwt_secret: str = ""
    site_origens: list[str] = field(default_factory=list)
    site_url: str = ""
    pasta_aulas: Path = RAIZ_REPO / "aulas-exemplo"
    limite_mensagens_dia: int = 60
    limite_aulas_dia: int = 5

    @property
    def jwks_url(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


@lru_cache
def config() -> Config:
    return Config(
        database_url=os.environ.get("DATABASE_URL", ""),
        supabase_url=os.environ.get("SUPABASE_URL", ""),
        supabase_service_key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
        supabase_jwt_secret=os.environ.get("SUPABASE_JWT_SECRET", ""),
        site_origens=_lista(os.environ.get("SITE_ORIGENS", "http://localhost:3000")),
        site_url=os.environ.get("SITE_URL", "http://localhost:3000"),
        pasta_aulas=Path(os.environ.get("PASTA_AULAS", str(RAIZ_REPO / "aulas-exemplo"))),
        limite_mensagens_dia=int(os.environ.get("LIMITE_MENSAGENS_DIA", "60")),
        limite_aulas_dia=int(os.environ.get("LIMITE_AULAS_DIA", "5")),
    )
