from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.ticket_history import TicketHistory
    from app.models.user import User


class Ticket(Base):
    __tablename__ = "tickets"

    __table_args__ = (
        CheckConstraint(
            "status IN "
            "('open', 'in_progress', 'waiting', 'resolved', 'closed')",
            name="ck_tickets_status",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high', 'urgent')",
            name="ck_tickets_priority",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20),
        default="open",
        server_default=text("'open'"),
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        server_default=text("'medium'"),
        nullable=False,
    )

    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    requester: Mapped[User] = relationship(
        back_populates="created_tickets",
        foreign_keys=[requester_id],
    )
    assignee: Mapped[User | None] = relationship(
        back_populates="assigned_tickets",
        foreign_keys=[assignee_id],
    )
    history: Mapped[list[TicketHistory]] = relationship(
        back_populates="ticket",
        cascade="all, delete-orphan",
    )