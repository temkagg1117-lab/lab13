# app/models/task.py

from datetime import date
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Priority(str, PyEnum):
    low = "low"
    medium = "medium"
    high = "high"


# Many-to-many association table — tasks ↔ labels
task_labels = Table(
    "task_labels",
    Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", Integer, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    tasks: Mapped[list["Task"]] = relationship(
        "Task", secondary=task_labels, back_populates="labels"
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority_enum"),
        default=Priority.medium,
        nullable=False,
        index=True,
    )

    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    labels: Mapped[list[Label]] = relationship(
        "Label", secondary=task_labels, back_populates="tasks"
    )

    def __repr__(self) -> str:
        return (
            f"<Task id={self.id} title={self.title!r} "
            f"priority={self.priority.value} completed={self.completed}>"
        )