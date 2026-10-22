from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

TicketPriority = Literal["low", "medium", "high", "urgent"]
TicketStatus = Literal[
    "open",
    "in_progress",
    "waiting",
    "resolved",
    "closed",
]


class TicketCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=1, max_length=10_000)
    priority: TicketPriority = "medium"


class TicketUpdate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str | None = Field(default=None, min_length=3, max_length=160)
    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=10_000,
    )
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assignee_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_patch_fields(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Informe ao menos um campo para atualizar.")

        for field_name in ("title", "description", "status", "priority"):
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(f"{field_name} não pode ser nulo.")

        return self


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    requester_id: int
    assignee_id: int | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None