from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip() -> None:
    password = "Uma-Senha-Forte-de-Teste-938!"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert hashed_password.startswith("$argon2id$")
    assert verify_password(password, hashed_password)


def test_password_hash_rejects_wrong_password() -> None:
    hashed_password = hash_password("Senha-Correta-123!")

    assert not verify_password("Senha-Errada-456!", hashed_password)


def test_access_token_contains_subject_and_expiration() -> None:
    token = create_access_token(subject="42")

    payload = decode_access_token(token)

    assert payload["sub"] == "42"
    assert payload["type"] == "access"
    assert payload["exp"] > payload["iat"]


def test_expired_access_token_is_rejected() -> None:
    token = create_access_token(
        subject="42",
        expires_delta=timedelta(seconds=-1),
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_invalid_signature_is_rejected() -> None:
    settings = get_settings()
    now = datetime.now(UTC)

    token = jwt.encode(
        {
            "sub": "42",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "type": "access",
        },
        "this-is-not-the-configured-secret",
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


def test_non_access_token_is_rejected() -> None:
    settings = get_settings()
    now = datetime.now(UTC)

    token = jwt.encode(
        {
            "sub": "42",
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "type": "refresh",
        },
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.InvalidTokenError, match="Tipo de token inválido"):
        decode_access_token(token)