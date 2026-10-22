from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()

# Usado quando o e-mail não existe para reduzir diferenças no tempo de login.
DUMMY_PASSWORD_HASH = password_hash.hash(
    "dummy-password-used-only-to-check-login-timing"
)


def hash_password(password: str) -> str:
    """Gera um hash Argon2 para armazenar a senha."""
    if not password:
        raise ValueError("A senha não pode ser vazia.")

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verifica uma senha em relação ao hash armazenado."""
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Cria um JWT de acesso com identificação e expiração."""
    if not subject or not subject.strip():
        raise ValueError("O identificador do usuário não pode ser vazio.")

    settings = get_settings()
    now = datetime.now(UTC)

    lifetime = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.access_token_expire_minutes)
    )

    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + lifetime,
        "type": "access",
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Valida um JWT e retorna suas informações."""
    settings = get_settings()

    payload = jwt.decode(
        token,
        settings.jwt_secret_key.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "iat", "sub", "type"]},
    )

    subject = payload.get("sub")

    if not isinstance(subject, str) or not subject:
        raise jwt.InvalidTokenError("Identificador de usuário inválido.")

    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Tipo de token inválido.")

    return payload