
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models import User


def create_ticket(
    client: TestClient,
    title: str,
) -> dict[str, object]:
    response = client.post(
        "/tickets",
        json={
            "title": title,
            "description": f"Descrição do chamado: {title}.",
        },
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_requester_can_create_and_list_own_comments(ticket_client) -> None:
    client, requester_id, _ = ticket_client
    ticket = create_ticket(client, "Chamado com comentários")

    first_response = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "Já reiniciei o sistema."},
    )

    assert first_response.status_code == 201, first_response.text

    first_comment = first_response.json()
    assert first_comment["ticket_id"] == ticket["id"]
    assert first_comment["author_id"] == requester_id
    assert first_comment["content"] == "Já reiniciei o sistema."
    assert first_comment["created_at"] is not None

    second_response = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "O problema continua."},
    )

    assert second_response.status_code == 201, second_response.text

    response = client.get(f"/tickets/{ticket['id']}/comments")

    assert response.status_code == 200
    comments = response.json()

    assert len(comments) == 2
    assert comments[0]["content"] == "Já reiniciei o sistema."
    assert comments[1]["content"] == "O problema continua."


def test_staff_can_comment_on_ticket(staff_client) -> None:
    client, staff_id, _ = staff_client
    ticket = create_ticket(client, "Chamado para atendimento")

    response = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "Estamos analisando o problema."},
    )

    assert response.status_code == 201, response.text
    assert response.json()["author_id"] == staff_id


def test_requester_cannot_access_another_users_comments(
    ticket_client,
) -> None:
    client, _, session_factory = ticket_client
    ticket = create_ticket(client, "Chamado privado")

    comment_response = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "Comentário privado."},
    )
    assert comment_response.status_code == 201

    with session_factory() as db:
        another_user = User(
            name="Outro solicitante",
            email="comments-requester@example.com",
            password_hash="test-hash",
            role="requester",
        )
        db.add(another_user)
        db.commit()
        db.refresh(another_user)
        another_user_id = another_user.id

    client.headers.update(
        {
            "Authorization": (
                f"Bearer {create_access_token(str(another_user_id))}"
            )
        }
    )

    get_response = client.get(f"/tickets/{ticket['id']}/comments")

    assert get_response.status_code == 404
    assert get_response.json()["detail"] == "Chamado não encontrado."

    post_response = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "Tentativa de comentário não autorizado."},
    )

    assert post_response.status_code == 404
    assert post_response.json()["detail"] == "Chamado não encontrado."


def test_comments_return_404_for_unknown_ticket(staff_client) -> None:
    client, _, _ = staff_client

    get_response = client.get("/tickets/9999/comments")
    assert get_response.status_code == 404

    post_response = client.post(
        "/tickets/9999/comments",
        json={"content": "Comentário em chamado inexistente."},
    )
    assert post_response.status_code == 404


def test_create_comment_rejects_blank_content(ticket_client) -> None:
    client, _, _ = ticket_client
    ticket = create_ticket(client, "Chamado com comentário inválido")

    response = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "   "},
    )

    assert response.status_code == 422


def test_create_comment_rejects_content_over_5000_characters(
    ticket_client,
) -> None:
    client, _, _ = ticket_client
    ticket = create_ticket(client, "Chamado com comentário longo")

    response = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"content": "x" * 5001},
    )

    assert response.status_code == 422
