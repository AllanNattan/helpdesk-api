from sqlalchemy.orm import configure_mappers

from app.core.database import Base
from app.models import Ticket, TicketHistory, User


def test_all_models_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "users",
        "tickets",
        "ticket_history",
    }


def test_user_model_has_required_constraints() -> None:
    users = User.__table__
    constraint_names = {constraint.name for constraint in users.constraints}

    assert users.c.email.unique is True
    assert "ck_users_role" in constraint_names
    assert users.c.password_hash.nullable is False


def test_ticket_model_has_status_and_priority_constraints() -> None:
    tickets = Ticket.__table__
    constraint_names = {
        constraint.name for constraint in tickets.constraints
    }

    assert "ck_tickets_status" in constraint_names
    assert "ck_tickets_priority" in constraint_names
    assert tickets.c.requester_id.nullable is False
    assert tickets.c.assignee_id.nullable is True


def test_ticket_foreign_keys_have_expected_delete_rules() -> None:
    tickets = Ticket.__table__

    requester_fk = next(iter(tickets.c.requester_id.foreign_keys))
    assignee_fk = next(iter(tickets.c.assignee_id.foreign_keys))

    assert requester_fk.target_fullname == "users.id"
    assert requester_fk.ondelete == "RESTRICT"
    assert assignee_fk.target_fullname == "users.id"
    assert assignee_fk.ondelete == "SET NULL"


def test_history_foreign_keys_have_expected_delete_rules() -> None:
    history = TicketHistory.__table__

    ticket_fk = next(iter(history.c.ticket_id.foreign_keys))
    changed_by_fk = next(iter(history.c.changed_by_id.foreign_keys))

    assert ticket_fk.target_fullname == "tickets.id"
    assert ticket_fk.ondelete == "CASCADE"
    assert changed_by_fk.target_fullname == "users.id"
    assert changed_by_fk.ondelete == "SET NULL"


def test_model_relationships_are_valid() -> None:
    configure_mappers()

    assert "requester" in Ticket.__mapper__.relationships
    assert "assignee" in Ticket.__mapper__.relationships
    assert "history" in Ticket.__mapper__.relationships
    assert "created_tickets" in User.__mapper__.relationships