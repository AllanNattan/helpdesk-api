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


def test_history_returns_ticket_changes(staff_client) -> None:
    client, staff_id, _ = staff_client
    ticket = create_ticket(client, "Chamado para consultar histórico")

    update_response = client.patch(
        f"/tickets/{ticket['id']}",
        json={"status": "in_progress"},
    )
    assert update_response.status_code == 200

    response = client.get(f"/tickets/{ticket['id']}/history")

    assert response.status_code == 200
    history = response.json()

    assert len(history) == 1
    assert history[0]["ticket_id"] == ticket["id"]
    assert history[0]["changed_by_id"] == staff_id
    assert history[0]["field_name"] == "status"
    assert history[0]["old_value"] == "open"
    assert history[0]["new_value"] == "in_progress"
    assert history[0]["created_at"] is not None


def test_requester_can_view_own_ticket_history(ticket_client) -> None:
    client, requester_id, _ = ticket_client
    ticket = create_ticket(client, "Chamado do solicitante")

    update_response = client.patch(
        f"/tickets/{ticket['id']}",
        json={"title": "Título atualizado"},
    )
    assert update_response.status_code == 200

    response = client.get(f"/tickets/{ticket['id']}/history")

    assert response.status_code == 200
    history = response.json()

    assert len(history) == 1
    assert history[0]["field_name"] == "title"
    assert history[0]["old_value"] == "Chamado do solicitante"
    assert history[0]["new_value"] == "Título atualizado"
    assert history[0]["changed_by_id"] == requester_id


def test_requester_cannot_view_another_users_history(
    ticket_client,
) -> None:
    client, _, session_factory = ticket_client
    ticket = create_ticket(client, "Chamado privado")

    with session_factory() as db:
        another_user = User(
            name="Outro solicitante",
            email="history-requester@example.com",
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

    response = client.get(f"/tickets/{ticket['id']}/history")

    assert response.status_code == 404
    assert response.json()["detail"] == "Chamado não encontrado."


def test_history_returns_404_for_unknown_ticket(staff_client) -> None:
    client, _, _ = staff_client

    response = client.get("/tickets/9999/history")

    assert response.status_code == 404
    assert response.json()["detail"] == "Chamado não encontrado."