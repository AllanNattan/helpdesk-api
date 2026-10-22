
from fastapi.testclient import TestClient


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


def test_requester_cannot_change_ticket_priority(ticket_client) -> None:
    client, _, _ = ticket_client
    ticket = create_ticket(client, "Chamado com prioridade protegida")

    response = client.patch(
        f"/tickets/{ticket['id']}",
        json={"priority": "urgent"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Você não tem permissão para alterar esses campos."
    )


def test_requester_cannot_assign_ticket(ticket_client) -> None:
    client, _, _ = ticket_client
    ticket = create_ticket(client, "Chamado sem responsável")

    response = client.patch(
        f"/tickets/{ticket['id']}",
        json={"assignee_id": 9999},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Você não tem permissão para alterar esses campos."
    )


def test_forbidden_field_does_not_partially_update_ticket(
    ticket_client,
) -> None:
    client, _, _ = ticket_client
    original_title = "Título original"
    ticket = create_ticket(client, original_title)

    response = client.patch(
        f"/tickets/{ticket['id']}",
        json={
            "title": "Título que não deve ser salvo",
            "priority": "urgent",
        },
    )

    assert response.status_code == 403

    get_response = client.get(f"/tickets/{ticket['id']}")

    assert get_response.status_code == 200
    assert get_response.json()["title"] == original_title
    assert get_response.json()["priority"] == "medium"
