from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LabelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["Write ADR document"])
    description: Optional[str] = Field(None, max_length=2000, examples=["Document the stack decision"])
    due_date: Optional[date] = Field(None, examples=["2025-05-10"])
    priority: str = Field("medium", pattern="^(low|medium|high)$", examples=["high"])
    label_ids: list[int] = Field(default_factory=list, examples=[[1, 2]])

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v < date.today():
            raise ValueError("due_date cannot be in the past")
        return v

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title cannot be blank or whitespace only")
        return v.strip()

class TaskUpdate(BaseModel):
    """All fields optional — only provided fields are updated (PATCH semantics)."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[date] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    label_ids: Optional[list[int]] = None
    completed: Optional[bool] = None

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v < date.today():
            raise ValueError("due_date cannot be in the past")
        return v

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("title cannot be blank or whitespace only")
        return v.strip() if v else v

    def has_updates(self) -> bool:
        """Returns True if at least one field was provided."""
        return any(v is not None for v in self.model_dump().values())


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    due_date: Optional[date]
    priority: str
    completed: bool
    labels: list[LabelOut] = []

    @property
    def is_overdue(self) -> bool:
        """True if due_date has passed and task is not completed."""
        return (
            self.due_date is not None
            and self.due_date < date.today()
            and not self.completed
        )