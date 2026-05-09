# app/services/task_service.py

from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.task import Label, Priority, Task
from app.schemas.task import TaskCreate, TaskUpdate


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, task_id: int) -> Task:
    task = (
        db.query(Task)
        .options(joinedload(Task.labels))
        .filter(Task.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )
    return task


def _resolve_labels(db: Session, label_ids: list[int]) -> list[Label]:
    if not label_ids:
        return []
    labels = db.query(Label).filter(Label.id.in_(label_ids)).all()
    found_ids = {label.id for label in labels}
    missing = set(label_ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Label IDs not found: {sorted(missing)}",
        )
    return labels


# ── CREATE ────────────────────────────────────────────────────────────────────

def create_task(db: Session, data: TaskCreate) -> Task:
    labels = _resolve_labels(db, data.label_ids)
    task = Task(
        title=data.title,
        description=data.description,
        due_date=data.due_date,
        priority=Priority(data.priority),
        completed=False,
        labels=labels,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# ── READ (single) ─────────────────────────────────────────────────────────────

def get_task(db: Session, task_id: int) -> Task:
    return _get_or_404(db, task_id)


# ── READ (list + filter) ──────────────────────────────────────────────────────

def get_tasks(
    db: Session,
    *,
    q: Optional[str] = None,
    priority: Optional[str] = None,
    completed: Optional[bool] = None,
    label_id: Optional[int] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Task]:
    query = db.query(Task).options(joinedload(Task.labels))

    if q:
        query = query.filter(Task.title.ilike(f"%{q}%"))
    if priority:
        query = query.filter(Task.priority == Priority(priority))
    if completed is not None:
        query = query.filter(Task.completed == completed)
    if label_id:
        query = query.filter(Task.labels.any(Label.id == label_id))
    if due_before:
        query = query.filter(Task.due_date <= due_before)
    if due_after:
        query = query.filter(Task.due_date >= due_after)

    return query.order_by(Task.due_date.asc().nulls_last(), Task.id.asc()).offset(skip).limit(limit).all()


# ── UPDATE ────────────────────────────────────────────────────────────────────

def update_task(db: Session, task_id: int, data: TaskUpdate) -> Task:
    if not data.has_updates():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    task = _get_or_404(db, task_id)

    if data.title is not None:
        task.title = data.title
    if data.description is not None:
        task.description = data.description
    if data.due_date is not None:
        task.due_date = data.due_date
    if data.priority is not None:
        task.priority = Priority(data.priority)
    if data.completed is not None:
        task.completed = data.completed
    if data.label_ids is not None:
        task.labels = _resolve_labels(db, data.label_ids)

    db.commit()
    db.refresh(task)
    return task


# ── DELETE ────────────────────────────────────────────────────────────────────

def delete_task(db: Session, task_id: int) -> None:
    task = _get_or_404(db, task_id)
    db.delete(task)
    db.commit()


# ── COMPLETE (convenience) ────────────────────────────────────────────────────

def complete_task(db: Session, task_id: int) -> Task:
    task = _get_or_404(db, task_id)
    task.completed = True
    db.commit()
    db.refresh(task)
    return task