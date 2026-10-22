
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models import Ticket, TicketComment, TicketHistory, User
from app.schemas.ticket import (
    TicketCreate,
    TicketPriority,
    TicketRead,
    TicketStatus,
    TicketUpdate,
)
from app.schemas.ticket_comment import TicketCommentCreate, TicketCommentRead
from app.schemas.ticket_history import TicketHistoryRead

router = APIRouter(prefix="/tickets", tags=["Tickets"])

ALLOWED_STATUS_TRANSITIONS = {
    "open": {"in_progress"},
    "in_progress": {"waiting", "resolved"},
    "waiting": {"in_progress", "resolved"},
    "resolved": {"in_progress", "closed"},
    "closed": {"open"},
}

STAFF_ROLES = {"admin", "agent"}
REQUESTER_EDITABLE_FIELDS = {"title", "description"}


def serialize_history_value(value: object) -> str | None:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.isoformat()

    return str(value)


def ensure_ticket_access(ticket: Ticket, current_user: User) -> None:
    if (
        current_user.role == "requester"
        and ticket.requester_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado não encontrado.",
        )


@router.get("", response_model=list[TicketRead])
def list_tickets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    ticket_status: TicketStatus | None = Query(
        default=None,
        alias="status",
    ),
    priority: TicketPriority | None = Query(default=None),
) -> list[Ticket]:
    statement = select(Ticket)

    if current_user.role == "requester":
        statement = statement.where(
            Ticket.requester_id == current_user.id,
        )

    if ticket_status is not None:
        statement = statement.where(Ticket.status == ticket_status)

    if priority is not None:
        statement = statement.where(Ticket.priority == priority)

    statement = (
        statement
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


@router.get("/{ticket_id}", response_model=TicketRead)
def get_ticket(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Ticket:
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado não encontrado.",
        )

    ensure_ticket_access(ticket, current_user)
    return ticket


@router.get(
    "/{ticket_id}/comments",
    response_model=list[TicketCommentRead],
)
def get_ticket_comments(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TicketComment]:
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado não encontrado.",
        )

    ensure_ticket_access(ticket, current_user)

    statement = (
        select(TicketComment)
        .where(TicketComment.ticket_id == ticket_id)
        .order_by(
            TicketComment.created_at.asc(),
            TicketComment.id.asc(),
        )
    )

    return list(db.scalars(statement).all())


@router.post(
    "/{ticket_id}/comments",
    response_model=TicketCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket_comment(
    ticket_id: int,
    comment_data: TicketCommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TicketComment:
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado não encontrado.",
        )

    ensure_ticket_access(ticket, current_user)

    comment = TicketComment(
        ticket_id=ticket.id,
        author_id=current_user.id,
        content=comment_data.content,
    )
    db.add(comment)

    try:
        db.commit()
        db.refresh(comment)

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar o comentário.",
        ) from exc

    return comment


@router.get(
    "/{ticket_id}/history",
    response_model=list[TicketHistoryRead],
)
def get_ticket_history(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TicketHistory]:
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado não encontrado.",
        )

    ensure_ticket_access(ticket, current_user)

    statement = (
        select(TicketHistory)
        .where(TicketHistory.ticket_id == ticket_id)
        .order_by(
            TicketHistory.created_at.asc(),
            TicketHistory.id.asc(),
        )
    )

    return list(db.scalars(statement).all())


@router.patch("/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Ticket:
    ticket = db.get(Ticket, ticket_id)

    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chamado não encontrado.",
        )

    ensure_ticket_access(ticket, current_user)

    changes = ticket_data.model_dump(exclude_unset=True)

    if current_user.role not in STAFF_ROLES:
        forbidden_fields = set(changes) - REQUESTER_EDITABLE_FIELDS

        if forbidden_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para alterar esses campos.",
            )

    requested_status = changes.get("status", ticket.status)

    if ticket.status == "closed" and (
        requested_status != "open" or set(changes) != {"status"}
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Chamado encerrado. Reabra-o antes de fazer alterações.",
        )

    if (
        requested_status != ticket.status
        and requested_status
        not in ALLOWED_STATUS_TRANSITIONS[ticket.status]
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Transição de status não permitida: "
                f"{ticket.status} -> {requested_status}."
            ),
        )

    if "assignee_id" in changes and changes["assignee_id"] is not None:
        assignee = db.get(User, changes["assignee_id"])

        if assignee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Responsável não encontrado.",
            )

        if assignee.role not in STAFF_ROLES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="O responsável precisa ser um agente ou administrador.",
            )

    try:
        for field_name, new_value in changes.items():
            old_value = getattr(ticket, field_name)

            if old_value == new_value:
                continue

            db.add(
                TicketHistory(
                    ticket_id=ticket.id,
                    changed_by_id=current_user.id,
                    field_name=field_name,
                    old_value=serialize_history_value(old_value),
                    new_value=serialize_history_value(new_value),
                )
            )

            setattr(ticket, field_name, new_value)

            if field_name == "status":
                if new_value == "closed":
                    ticket.closed_at = datetime.now(UTC)
                elif old_value == "closed" and new_value == "open":
                    ticket.closed_at = None

        db.commit()
        db.refresh(ticket)

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível atualizar o chamado.",
        ) from exc

    return ticket


@router.post(
    "",
    response_model=TicketRead,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    ticket_data: TicketCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Ticket:
    ticket = Ticket(
        **ticket_data.model_dump(),
        requester_id=current_user.id,
    )
    db.add(ticket)

    try:
        db.commit()
        db.refresh(ticket)

    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível salvar o chamado.",
        ) from exc

    return ticket
