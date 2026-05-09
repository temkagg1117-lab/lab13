# app/routers/tasks.py

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ── POST /tasks ───────────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(data: TaskCreate, db: Session = Depends(get_db)) -> TaskResponse:
    return task_service.create_task(db, data)


# ── GET /tasks ────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=list[TaskResponse],
    summary="List tasks with optional filters",
)
def list_tasks(
    q: Optional[str] = Query(None, description="Search by title"),
    priority: Optional[str] = Query(None, pattern="^(low|medium|high)$"),
    completed: Optional[bool] = Query(None),
    label_id: Optional[int] = Query(None, description="Filter by label ID"),
    due_before: Optional[date] = Query(None, description="Tasks due on or before this date"),
    due_after: Optional[date] = Query(None, description="Tasks due on or after this date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[TaskResponse]:
    return task_service.get_tasks(
        db,
        q=q,
        priority=priority,
        completed=completed,
        label_id=label_id,
        due_before=due_before,
        due_after=due_after,
        skip=skip,
        limit=limit,
    )


# ── GET /tasks/{task_id} ──────────────────────────────────────────────────────

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a single task by ID",
)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskResponse:
    return task_service.get_task(db, task_id)


# ── PATCH /tasks/{task_id} ────────────────────────────────────────────────────

@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Partially update a task",
)
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
) -> TaskResponse:
    return task_service.update_task(db, task_id, data)


# ── DELETE /tasks/{task_id} ───────────────────────────────────────────────────

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
def delete_task(task_id: int, db: Session = Depends(get_db)) -> None:
    task_service.delete_task(db, task_id)


# ── POST /tasks/{task_id}/complete ────────────────────────────────────────────

@router.post(
    "/{task_id}/complete",
    response_model=TaskResponse,
    summary="Mark a task as completed",
)
def complete_task(task_id: int, db: Session = Depends(get_db)) -> TaskResponse:
    return task_service.complete_task(db, task_id)