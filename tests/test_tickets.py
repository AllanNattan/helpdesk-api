from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import create_access_token
from app.models import TicketHistory, User


def create_ticket(
    client: TestClient,
    requester_id: int,
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

    assert response.status_code == 201
    data = response.json()
    assert data["requester_id"] == requester_id
    return data


def move_ticket_to_closed(
    client: TestClient,
    ticket_id: int,
) -> dict[str, object]:
    for new_status in ("in_progress", "resolved", "closed"):
        response = client.patch(
            f"/tickets/{ticket_id}",
            json={"status": new_status},
        )
        assert response.status_code == 200, response.text

    return response.json()


def test_create_ticket_returns_created_response(ticket_client) -> None:
    client, requester_id, _ = ticket_client
    data = create_ticket(
        client,
        requester_id,
        "Erro ao acessar o sistema",
        priority="high",
    )

    assert data["title"] == "Erro ao acessar o sistema"
    assert data["status"] == "open"
    assert data["priority"] == "high"
    assert data["requester_id"] == requester_id
    assert data["id"] is not None
    assert data["created_at"] is not None


def test_create_ticket_rejects_client_supplied_requester_id(
    ticket_client,
) -> None:
    client, _, _ = ticket_client

    response = client.post(
        "/tickets",
        json={
            "title": "Chamado de teste",
            "description": "O solicitante não deve ser escolhido pelo cliente.",
            "requester_id": 9999,
        },
    )

    assert response.status_code == 422


def test_create_ticket_rejects_invalid_priority(ticket_client) -> None:
    client, _, _ = ticket_client

    response = client.post(
        "/tickets",
        json={
            "title": "Chamado de teste",
            "description": "A prioridade fornecida é inválida.",
            "priority": "critical",
        },
    )

    assert response.status_code == 422


def test_list_tickets_returns_paginated_results(ticket_client) -> None:
    client, requester_id, _ = ticket_client
    create_ticket(client, requester_id, "Primeiro chamado")
    create_ticket(client, requester_id, "Segundo chamado")

    response = client.get("/tickets", params={"skip": 0, "limit": 1})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Segundo chamado"


def test_get_ticket_returns_existing_ticket(ticket_client) -> None:
    client, requester_id, _ = ticket_client
    created = create_ticket(client, requester_id, "Chamado para consulta")

    response = client.get(f"/tickets/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["title"] == "Chamado para consulta"


def test_get_ticket_returns_404_for_unknown_id(ticket_client) -> None:
    client, _, _ = ticket_client

    response = client.get("/tickets/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Chamado não encontrado."


def test_list_tickets_rejects_limit_above_maximum(ticket_client) -> None:
    client, _, _ = ticket_client

    response = client.get("/tickets", params={"limit": 101})

    assert response.status_code == 422


def test_update_ticket_records_status_history(staff_client) -> None:
    client, staff_id, session_factory = staff_client
    created = create_ticket(client, staff_id, "Chamado para histórico")

    response = client.patch(
        f"/tickets/{created['id']}",
        json={"status": "in_progress"},
    )

    assert response.status_code == 200

    with session_factory() as db:
        history = db.scalars(
            select(TicketHistory).where(
                TicketHistory.ticket_id == created["id"],
                TicketHistory.field_name == "status",
            )
        ).all()

    assert len(history) == 1
    assert history[0].old_value == "open"
    assert history[0].new_value == "in_progress"
    assert history[0].changed_by_id == staff_id


def test_closing_ticket_sets_closed_at(staff_client) -> None:
    client, staff_id, _ = staff_client
    created = create_ticket(client, staff_id, "Chamado para encerramento")

    closed = move_ticket_to_closed(client, int(created["id"]))

    assert closed["status"] == "closed"
    assert closed["closed_at"] is not None


def test_update_ticket_can_remove_assignee(staff_client) -> None:
    client, staff_id, session_factory = staff_client
    created = create_ticket(client, staff_id, "Chamado com responsável")

    with session_factory() as db:
        agent = User(
            name="Segundo agente de teste",
            email="second-agent@example.com",
            password_hash="test-hash",
            role="agent",
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)
        agent_id = agent.id

    assigned = client.patch(
        f"/tickets/{created['id']}",
        json={"assignee_id": agent_id},
    )

    assert assigned.status_code == 200
    assert assigned.json()["assignee_id"] == agent_id

    unassigned = client.patch(
        f"/tickets/{created['id']}",
        json={"assignee_id": None},
    )

    assert unassigned.status_code == 200
    assert unassigned.json()["assignee_id"] is None


def test_update_ticket_rejects_invalid_status(ticket_client) -> None:
    client, requester_id, _ = ticket_client
    created = create_ticket(client, requester_id, "Chamado com status inválido")

    response = client.patch(
        f"/tickets/{created['id']}",
        json={"status": "cancelled"},
    )

    assert response.status_code == 422


def test_update_ticket_rejects_unknown_id(ticket_client) -> None:
    client, _, _ = ticket_client

    response = client.patch(
        "/tickets/9999",
        json={"status": "closed"},
    )

    assert response.status_code == 404


def test_update_ticket_rejects_empty_payload(ticket_client) -> None:
    client, requester_id, _ = ticket_client
    created = create_ticket(client, requester_id, "Chamado sem alterações")

    response = client.patch(f"/tickets/{created['id']}", json={})

    assert response.status_code == 422


def test_open_ticket_cannot_skip_directly_to_resolved(staff_client) -> None:
    client, staff_id, _ = staff_client
    created = create_ticket(client, staff_id, "Teste de transição inválida")

    response = client.patch(
        f"/tickets/{created['id']}",
        json={"status": "resolved"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Transição de status não permitida: open -> resolved."
    )


def test_open_ticket_cannot_be_closed_directly(staff_client) -> None:
    client, staff_id, _ = staff_client
    created = create_ticket(client, staff_id, "Teste de encerramento inválido")

    response = client.patch(
        f"/tickets/{created['id']}",
        json={"status": "closed"},
    )

    assert response.status_code == 409


def test_closing_resolved_ticket_sets_closed_at(staff_client) -> None:
    client, staff_id, _ = staff_client
    created = create_ticket(client, staff_id, "Teste de encerramento válido")

    closed = move_ticket_to_closed(client, int(created["id"]))

    assert closed["status"] == "closed"
    assert closed["closed_at"] is not None


def test_reopening_ticket_clears_closed_at(staff_client) -> None:
    client, staff_id, _ = staff_client
    created = create_ticket(client, staff_id, "Teste de reabertura")

    closed = move_ticket_to_closed(client, int(created["id"]))
    assert closed["closed_at"] is not None

    reopened = client.patch(
        f"/tickets/{created['id']}",
        json={"status": "open"},
    )

    assert reopened.status_code == 200
    assert reopened.json()["status"] == "open"
    assert reopened.json()["closed_at"] is None


def test_closed_ticket_requires_reopening_before_edit(staff_client) -> None:
    client, staff_id, _ = staff_client
    created = create_ticket(client, staff_id, "Teste de chamado encerrado")

    move_ticket_to_closed(client, int(created["id"]))

    response = client.patch(
        f"/tickets/{created['id']}",
        json={"title": "Tentativa de editar chamado encerrado"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Chamado encerrado. Reabra-o antes de fazer alterações."
    )


def test_requester_cannot_change_ticket_status(ticket_client) -> None:
    client, requester_id, _ = ticket_client
    created = create_ticket(client, requester_id, "Tentativa de mudança de status")

    response = client.patch(
        f"/tickets/{created['id']}",
        json={"status": "in_progress"},
    )

    assert response.status_code == 403


def test_requester_cannot_access_another_users_ticket(ticket_client) -> None:
    client, requester_id, session_factory = ticket_client
    created = create_ticket(client, requester_id, "Chamado privado")

    with session_factory() as db:
        another_user = User(
            name="Outro solicitante",
            email="another-requester@example.com",
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

    response = client.get(f"/tickets/{created['id']}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Chamado não encontrado."