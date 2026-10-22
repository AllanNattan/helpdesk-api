from sqlalchemy import select

from app.core.security import hash_password, verify_password
from app.models import User


def test_register_creates_user_with_hashed_password(ticket_client) -> None:
    client, _, session_factory = ticket_client
    password = "Senha-Forte-De-Teste-938!"
    email = "new-user@example.com"

    response = client.post(
        "/auth/register",
        json={
            "name": "Novo Usuário",
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["role"] == "requester"
    assert "password_hash" not in data
    assert "password" not in data

    with session_factory() as db:
        user = db.scalar(select(User).where(User.email == email))
        assert user is not None
        assert user.password_hash != password
        assert verify_password(password, user.password_hash)


def test_register_rejects_duplicate_email(ticket_client) -> None:
    client, _, _ = ticket_client

    response = client.post(
        "/auth/register",
        json={
            "name": "Usuário Duplicado",
            "email": "requester@example.com",
            "password": "Senha-Forte-De-Teste-938!",
        },
    )

    assert response.status_code == 409


def test_register_rejects_short_password(ticket_client) -> None:
    client, _, _ = ticket_client

    response = client.post(
        "/auth/register",
        json={
            "name": "Novo Usuário",
            "email": "short-password@example.com",
            "password": "curta",
        },
    )

    assert response.status_code == 422


def test_login_returns_token_and_me_returns_user(ticket_client) -> None:
    client, _, session_factory = ticket_client
    email = "login-user@example.com"
    password = "Senha-Forte-De-Teste-938!"

    with session_factory() as db:
        user = User(
            name="Usuário de Login",
            email=email,
            password_hash=hash_password(password),
        )
        db.add(user)
        db.commit()

    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )

    assert response.status_code == 200
    token_data = response.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token_data['access_token']}",
        },
    )

    assert me_response.status_code == 200
    assert me_response.json()["email"] == email
    assert me_response.json()["name"] == "Usuário de Login"
    assert "password_hash" not in me_response.json()


def test_login_rejects_incorrect_password(ticket_client) -> None:
    client, _, session_factory = ticket_client

    with session_factory() as db:
        user = User(
            name="Usuário de Teste",
            email="wrong-password@example.com",
            password_hash=hash_password("Senha-Correta-De-Teste-938!"),
        )
        db.add(user)
        db.commit()

    response = client.post(
        "/auth/login",
        data={
            "username": "wrong-password@example.com",
            "password": "Senha-Errada-938!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "E-mail ou senha inválidos."


def test_login_rejects_inactive_account(ticket_client) -> None:
    client, _, session_factory = ticket_client
    email = "inactive-user@example.com"
    password = "Senha-Forte-De-Teste-938!"

    with session_factory() as db:
        user = User(
            name="Usuário Inativo",
            email=email,
            password_hash=hash_password(password),
            is_active=False,
        )
        db.add(user)
        db.commit()

    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Conta desativada."


def test_me_rejects_missing_token(ticket_client) -> None:
    client, _, _ = ticket_client
    client.headers.pop("Authorization", None)

    response = client.get("/auth/me")

    assert response.status_code == 401