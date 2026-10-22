
from fastapi.testclient import TestClient


def create_ticket(
    client: TestClient,
    title: str,
) -> None:
    response = client.post(
        "/tickets",
        json={
            "title": title,
            "description": f"Descrição do chamado: {title}.",
        },
    )

    assert response.status_code == 201, response.text


def test_list_tickets_applies_skip_offset(ticket_client) -> None:
    client, _, _ = ticket_client

    create_ticket(client, "Chamado antigo")
    create_ticket(client, "Chamado intermediário")
    create_ticket(client, "Chamado mais recente")

    response = client.get(
        "/tickets",
        params={"skip": 1, "limit": 1},
    )

    assert response.status_code == 200
    tickets = response.json()

    assert len(tickets) == 1
    assert tickets[0]["title"] == "Chamado intermediário"


def test_list_tickets_rejects_negative_skip(ticket_client) -> None:
    client, _, _ = ticket_client

    response = client.get(
        "/tickets",
        params={"skip": -1},
    )

    assert response.status_code == 422


def test_list_tickets_rejects_zero_limit(ticket_client) -> None:
    client, _, _ = ticket_client

    response = client.get(
        "/tickets",
        params={"limit": 0},
    )

    assert response.status_code == 422
