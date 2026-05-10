import pytest
from datetime import date, timedelta
from typing import Generator, Optional
from enum import Enum as PyEnum
 
from fastapi import FastAPI, APIRouter, Depends, Query, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import create_engine, Boolean, Column, Date, Enum, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, joinedload, Session

 
class Base(DeclarativeBase):
    pass
 
class Priority(str, PyEnum):
    low = "low"
    medium = "medium"
    high = "high"
 
task_labels = Table(
    "task_labels", Base.metadata,
    Column("task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", Integer, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)
 
class Label(Base):
    __tablename__ = "labels"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    tasks: Mapped[list["Task"]] = relationship("Task", secondary=task_labels, back_populates="labels")
 
class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[Priority] = mapped_column(Enum(Priority, name="priority_enum"), default=Priority.medium)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    labels: Mapped[list[Label]] = relationship("Label", secondary=task_labels, back_populates="tasks")

class LabelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
 
class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    label_ids: list[int] = Field(default_factory=list)
 
    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v):
        if v is not None and v < date.today():
            raise ValueError("due_date cannot be in the past")
        return v
 
    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v):
        if not v.strip():
            raise ValueError("title cannot be blank")
        return v.strip()
 
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    label_ids: Optional[list[int]] = None
    completed: Optional[bool] = None
    def has_updates(self): return any(v is not None for v in self.model_dump().values())
 
class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: Optional[str]
    due_date: Optional[date]
    priority: str
    completed: bool
    labels: list[LabelOut] = []

def _get_or_404(db, task_id):
    t = db.query(Task).options(joinedload(Task.labels)).filter(Task.id == task_id).first()
    if not t:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return t
 
def _resolve_labels(db, ids):
    if not ids: return []
    labels = db.query(Label).filter(Label.id.in_(ids)).all()
    missing = set(ids) - {l.id for l in labels}
    if missing:
        raise HTTPException(status_code=422, detail=f"Label IDs not found: {sorted(missing)}")
    return labels
 
def svc_create(db, data):
    t = Task(title=data.title, description=data.description, due_date=data.due_date,
             priority=Priority(data.priority), completed=False, labels=_resolve_labels(db, data.label_ids))
    db.add(t); db.commit(); db.refresh(t); return t
 
def svc_get(db, tid): return _get_or_404(db, tid)
 
def svc_list(db, **kw):
    q = db.query(Task).options(joinedload(Task.labels))
    if kw.get("q"): q = q.filter(Task.title.ilike(f"%{kw['q']}%"))
    if kw.get("priority"): q = q.filter(Task.priority == Priority(kw["priority"]))
    if kw.get("completed") is not None: q = q.filter(Task.completed == kw["completed"])
    if kw.get("label_id"): q = q.filter(Task.labels.any(Label.id == kw["label_id"]))
    return q.order_by(Task.due_date.asc().nulls_last(), Task.id).offset(kw.get("skip", 0)).limit(kw.get("limit", 100)).all()
 
def svc_update(db, tid, data):
    if not data.has_updates():
        raise HTTPException(status_code=400, detail="No fields provided")
    t = _get_or_404(db, tid)
    if data.title is not None: t.title = data.title
    if data.description is not None: t.description = data.description
    if data.due_date is not None: t.due_date = data.due_date
    if data.priority is not None: t.priority = Priority(data.priority)
    if data.completed is not None: t.completed = data.completed
    if data.label_ids is not None: t.labels = _resolve_labels(db, data.label_ids)
    db.commit(); db.refresh(t); return t
 
def svc_delete(db, tid):
    t = _get_or_404(db, tid); db.delete(t); db.commit()
 
def svc_complete(db, tid):
    t = _get_or_404(db, tid); t.completed = True; db.commit(); db.refresh(t); return t

 
def get_db(): pass 
 
router = APIRouter(prefix="/tasks", tags=["Tasks"])
 
@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(data: TaskCreate, db: Session = Depends(get_db)): return svc_create(db, data)
 
@router.get("/", response_model=list[TaskResponse])
def list_tasks(q: Optional[str]=Query(None), priority: Optional[str]=Query(None, pattern="^(low|medium|high)$"),
               completed: Optional[bool]=Query(None), label_id: Optional[int]=Query(None),
               skip: int=Query(0, ge=0), limit: int=Query(100, ge=1, le=500), db: Session=Depends(get_db)):
    return svc_list(db, q=q, priority=priority, completed=completed, label_id=label_id, skip=skip, limit=limit)
 
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)): return svc_get(db, task_id)
 
@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)): return svc_update(db, task_id, data)
 
@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)): svc_delete(db, task_id)
 
@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(task_id: int, db: Session = Depends(get_db)): return svc_complete(db, task_id)
 
app = FastAPI()
app.include_router(router)