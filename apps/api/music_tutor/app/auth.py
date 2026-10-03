"""Confere o token de login do Supabase que o site manda em cada chamada."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Config, config

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Usuario:
    id: str
    email: str
    claims: dict


@lru_cache
def _jwks(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url, cache_keys=True)


def decodificar(token: str, cfg: Config) -> dict:
    opcoes = {"require": ["sub", "exp"]}
    if cfg.supabase_jwt_secret:
        return jwt.decode(token, cfg.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated", options=opcoes)
    if not cfg.supabase_url:
        raise RuntimeError("defina SUPABASE_URL (chaves JWKS) ou SUPABASE_JWT_SECRET")
    chave = _jwks(cfg.jwks_url).get_signing_key_from_jwt(token)
    return jwt.decode(token, chave.key, algorithms=["ES256", "RS256"], audience="authenticated", options=opcoes)


def usuario_logado(cred: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> Usuario:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "faça login", headers={"WWW-Authenticate": "Bearer"})
    try:
        claims = decodificar(cred.credentials, config())
    except (jwt.InvalidTokenError, jwt.PyJWKClientError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "sessão inválida ou expirada", headers={"WWW-Authenticate": "Bearer"})
    if claims.get("role") != "authenticated":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "sessão inválida")
    return Usuario(id=claims["sub"], email=claims.get("email", ""), claims=claims)
