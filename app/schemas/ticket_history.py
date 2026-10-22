from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    changed_by_id: int | None
    field_name: str
    old_value: str | None
    new_value: str | None
    created_at: datetime