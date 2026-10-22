from fastapi.testclient import TestClient


def create_ticket(
    client: TestClient,
    title: str,
    priority: str = "medium",
) -> dict[str, object]:
    response = client.post(
        "/tickets",
        json={
            "title": title,
            "description": f"Descrição do chamado: {title}.",
            "priority": priority,
        },
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_list_tickets_filters_by_status(staff_client) -> None:
    client, _, _ = staff_client

    create_ticket(client, "Chamado aberto")
    in_progress = create_ticket(client, "Chamado em andamento")

    update_response = client.patch(
        f"/tickets/{in_progress['id']}",
        json={"status": "in_progress"},
    )
    assert update_response.status_code == 200

    response = client.get(
        "/tickets",
        params={"status": "in_progress"},
    )

    assert response.status_code == 200
    tickets = response.json()
    assert len(tickets) == 1
    assert tickets[0]["id"] == in_progress["id"]


def test_list_tickets_filters_by_priority(staff_client) -> None:
    client, _, _ = staff_client

    create_ticket(client, "Chamado de baixa prioridade", "low")
    urgent = create_ticket(client, "Chamado urgente", "urgent")

    response = client.get(
        "/tickets",
        params={"priority": "urgent"},
    )

    assert response.status_code == 200
    tickets = response.json()
    assert len(tickets) == 1
    assert tickets[0]["id"] == urgent["id"]


def test_list_tickets_combines_status_and_priority(staff_client) -> None:
    client, _, _ = staff_client

    target = create_ticket(client, "Urgente em andamento", "urgent")
    other_priority = create_ticket(client, "Baixa em andamento", "low")
    other_status = create_ticket(client, "Urgente aberto", "urgent")

    for ticket in (target, other_priority):
        response = client.patch(
            f"/tickets/{ticket['id']}",
            json={"status": "in_progress"},
        )
        assert response.status_code == 200

    response = client.get(
        "/tickets",
        params={
            "status": "in_progress",
            "priority": "urgent",
        },
    )

    assert response.status_code == 200
    tickets = response.json()
    assert len(tickets) == 1
    assert tickets[0]["id"] == target["id"]
    assert tickets[0]["id"] != other_status["id"]


def test_list_tickets_rejects_invalid_status(staff_client) -> None:
    client, _, _ = staff_client

    response = client.get(
        "/tickets",
        params={"status": "cancelled"},
    )

    assert response.status_code == 422


def test_list_tickets_rejects_invalid_priority(staff_client) -> None:
    client, _, _ = staff_client

    response = client.get(
        "/tickets",
        params={"priority": "critical"},
    )

    assert response.status_code == 422