
import asyncio
import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str | None


def _supabase_get(
    path: str,
    access_token: str,
) -> dict:
    """
    Executa uma consulta autenticada ao Supabase.

    A publishable key identifica o projeto.
    O Bearer token representa o usuário.
    """
    url = f"{settings.SUPABASE_URL.rstrip('/')}{path}"

    request = Request(
        url,
        method="GET",
        headers={
            "apikey": settings.SUPABASE_PUBLISHABLE_KEY,
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    except HTTPError as exc:
        if exc.code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sessão inválida ou expirada.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar a sessão no Supabase.",
        ) from exc

    except (URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de autenticação indisponível.",
        ) from exc


def _validate_user(access_token: str) -> CurrentUser:
    """
    Valida o token no Supabase Auth e verifica
    o status do perfil no banco.
    """
    auth_data = _supabase_get(
        "/auth/v1/user",
        access_token,
    )

    user_id = auth_data.get("id")

    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível identificar o usuário.",
        )

    email = auth_data.get("email")

    # O filtro por ID é redundante com a política RLS,
    # mas deixa explícita a intenção da consulta.
    encoded_id = quote(user_id, safe="")

    profile_data = _supabase_get(
        (
            "/rest/v1/profiles"
            f"?select=id,access_status&id=eq.{encoded_id}"
        ),
        access_token,
    )

    if not isinstance(profile_data, list) or len(profile_data) != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Perfil não encontrado ou acesso não autorizado.",
        )

    profile = profile_data[0]

    if profile.get("id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Perfil inválido.",
        )

    if profile.get("access_status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu acesso não está ativo.",
        )

    return CurrentUser(
        id=user_id,
        email=email if isinstance(email, str) else None,
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> CurrentUser:
    """
    Dependência FastAPI reutilizável.

    Bloqueia requisições sem token ou com token inválido.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação obrigatória.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Esquema de autenticação inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await asyncio.to_thread(_validate_user, token)
