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

import tempfile, os
 
@pytest.fixture(scope="function")
def db_session() -> Generator:
    """Fresh SQLite file per test — full isolation."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        os.unlink(path)
 
@pytest.fixture(scope="function")
def client(db_session) -> Generator:
    """TestClient wired to isolated test DB."""
    def override():
        yield db_session
    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
 
@pytest.fixture
def future_date() -> str:
    return (date.today() + timedelta(days=7)).isoformat()
 
@pytest.fixture
def past_date() -> str:
    return (date.today() - timedelta(days=1)).isoformat()
 
@pytest.fixture
def task(client, future_date) -> dict:
    """A single pre-created task for tests that need an existing record."""
    r = client.post("/tasks/", json={"title": "Default task", "priority": "medium", "due_date": future_date})
    assert r.status_code == 201
    return r.json()
 
 
# ── CRUD Tests ────────────────────────────────────────────────────────────────
 
class TestCreateTask:
    def test_create_task_success(self, client, future_date):
        """TC-01: Valid payload returns 201 with all fields."""
        r = client.post("/tasks/", json={
            "title": "Buy groceries",
            "description": "Milk and eggs",
            "priority": "high",
            "due_date": future_date,
        })
        assert r.status_code == 201
        body = r.json()
        assert body["title"] == "Buy groceries"
        assert body["priority"] == "high"
        assert body["completed"] is False
        assert body["id"] is not None
 
    def test_create_task_missing_title(self, client):
        """TC-02: Missing title returns 422."""
        r = client.post("/tasks/", json={"priority": "low"})
        assert r.status_code == 422
 
    def test_create_task_blank_title(self, client):
        """TC-03: Whitespace-only title returns 422."""
        r = client.post("/tasks/", json={"title": "   "})
        assert r.status_code == 422
 
    def test_create_task_defaults(self, client):
        """TC-04: Omitted optional fields use correct defaults."""
        r = client.post("/tasks/", json={"title": "Minimal task"})
        assert r.status_code == 201
        body = r.json()
        assert body["priority"] == "medium"
        assert body["completed"] is False
        assert body["due_date"] is None
        assert body["labels"] == []
 
 
class TestGetTask:
    def test_get_tasks_empty(self, client):
        """TC-05: Empty DB returns empty list."""
        r = client.get("/tasks/")
        assert r.status_code == 200
        assert r.json() == []
 
    def test_get_tasks_returns_all(self, client, future_date):
        """TC-06: All created tasks appear in list."""
        client.post("/tasks/", json={"title": "Task A"})
        client.post("/tasks/", json={"title": "Task B"})
        r = client.get("/tasks/")
        assert r.status_code == 200
        assert len(r.json()) == 2
 
    def test_get_task_by_id(self, client, task):
        """TC-07: Existing task is returned correctly by ID."""
        r = client.get(f"/tasks/{task['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == task["id"]
 
    def test_get_task_not_found(self, client):
        """TC-08: Non-existent ID returns 404."""
        r = client.get("/tasks/99999")
        assert r.status_code == 404
     
class TestUpdateTask:
    def test_update_task_title(self, client, task):
        """TC-09: PATCH title updates only that field."""
        r = client.patch(f"/tasks/{task['id']}", json={"title": "Updated title"})
        assert r.status_code == 200
        assert r.json()["title"] == "Updated title"
        assert r.json()["priority"] == task["priority"]  
 
    def test_update_task_not_found(self, client):
        """TC-10: PATCH on non-existent task returns 404."""
        r = client.patch("/tasks/99999", json={"title": "Ghost"})
        assert r.status_code == 404
 
    def test_update_task_empty_body(self, client, task):
        """TC-11: PATCH with no fields returns 400."""
        r = client.patch(f"/tasks/{task['id']}", json={})
        assert r.status_code == 400
 
    def test_update_task_priority(self, client, task):
        """TC-12: Priority can be changed via PATCH."""
        r = client.patch(f"/tasks/{task['id']}", json={"priority": "low"})
        assert r.status_code == 200
        assert r.json()["priority"] == "low"
 
 
class TestDeleteTask:
    def test_delete_task_success(self, client, task):
        """TC-13: DELETE returns 204 and task is gone."""
        r = client.delete(f"/tasks/{task['id']}")
        assert r.status_code == 204
        r2 = client.get(f"/tasks/{task['id']}")
        assert r2.status_code == 404
 
    def test_delete_task_not_found(self, client):
        """TC-14: DELETE non-existent task returns 404."""
        r = client.delete("/tasks/99999")
        assert r.status_code == 404
 
    def test_delete_task_idempotency(self, client, task):
        """TC-15: Deleting same task twice — second call returns 404."""
        client.delete(f"/tasks/{task['id']}")
        r = client.delete(f"/tasks/{task['id']}")
        assert r.status_code == 404
 
class TestValidation:
    def test_invalid_due_date_in_past(self, client, past_date):
        """TC-16: Past due_date returns 422."""
        r = client.post("/tasks/", json={"title": "Late task", "due_date": past_date})
        assert r.status_code == 422
 
    def test_invalid_due_date_format(self, client):
        """TC-17: Malformed date string returns 422."""
        r = client.post("/tasks/", json={"title": "Bad date", "due_date": "not-a-date"})
        assert r.status_code == 422
 
    def test_invalid_priority_value(self, client):
        """TC-18: Unknown priority string returns 422."""
        r = client.post("/tasks/", json={"title": "Task", "priority": "urgent"})
        assert r.status_code == 422
 
    def test_title_too_long(self, client):
        """TC-19: Title exceeding 255 chars returns 422."""
        r = client.post("/tasks/", json={"title": "x" * 256})
        assert r.status_code == 422
 
    def test_complete_task_marks_done(self, client, task):
        """TC-20: POST /complete sets completed=True."""
        r = client.post(f"/tasks/{task['id']}/complete")
        assert r.status_code == 200
        assert r.json()["completed"] is True
class TestSearchAndFilter:
    def test_search_by_keyword_match(self, client):
        """TC-21: ?q= returns tasks whose title contains the keyword."""
        client.post("/tasks/", json={"title": "Buy groceries"})
        client.post("/tasks/", json={"title": "Call doctor"})
        r = client.get("/tasks/?q=groceries")
        assert r.status_code == 200
        titles = [t["title"] for t in r.json()]
        assert "Buy groceries" in titles
        assert "Call doctor" not in titles
 
    def test_search_by_keyword_no_match(self, client):
        """TC-22: ?q= with no matching tasks returns empty list."""
        client.post("/tasks/", json={"title": "Buy groceries"})
        r = client.get("/tasks/?q=zzznomatch")
        assert r.status_code == 200
        assert r.json() == []
 
    def test_search_case_insensitive(self, client):
        """TC-23: Keyword search is case-insensitive."""
        client.post("/tasks/", json={"title": "Buy Groceries"})
        r = client.get("/tasks/?q=groceries")
        assert len(r.json()) == 1
 
    def test_filter_by_priority_high(self, client, future_date):
        """TC-24: ?priority=high returns only high-priority tasks."""
        client.post("/tasks/", json={"title": "High task", "priority": "high", "due_date": future_date})
        client.post("/tasks/", json={"title": "Low task", "priority": "low"})
        r = client.get("/tasks/?priority=high")
        assert r.status_code == 200
        assert all(t["priority"] == "high" for t in r.json())
        assert len(r.json()) == 1
 
    def test_filter_by_priority_invalid(self, client):
        """TC-25: ?priority=urgent returns 422."""
        r = client.get("/tasks/?priority=urgent")
        assert r.status_code == 422
 
    def test_filter_completed_false(self, client, task):
        """TC-26: ?completed=false excludes completed tasks."""
        client.post(f"/tasks/{task['id']}/complete")
        r = client.get("/tasks/?completed=false")
        ids = [t["id"] for t in r.json()]
        assert task["id"] not in ids
 
    def test_filter_completed_true(self, client, task):
        """TC-27: ?completed=true returns only completed tasks."""
        client.post(f"/tasks/{task['id']}/complete")
        r = client.get("/tasks/?completed=true")
        assert r.status_code == 200
        assert all(t["completed"] is True for t in r.json())
        assert any(t["id"] == task["id"] for t in r.json())
 
    def test_filter_combined(self, client, future_date):
        """TC-28: Multiple filters applied together narrow results correctly."""
        client.post("/tasks/", json={"title": "Report", "priority": "high", "due_date": future_date})
        client.post("/tasks/", json={"title": "Report draft", "priority": "low"})
        client.post("/tasks/", json={"title": "Unrelated", "priority": "high", "due_date": future_date})
        r = client.get("/tasks/?q=report&priority=high")
        assert r.status_code == 200
        results = r.json()
        assert len(results) == 1
        assert results[0]["title"] == "Report"

class TestPagination:
    def test_limit_parameter(self, client):
        """TC-29: ?limit=2 returns at most 2 tasks."""
        for i in range(5):
            client.post("/tasks/", json={"title": f"Task {i}"})
        r = client.get("/tasks/?limit=2")
        assert r.status_code == 200
        assert len(r.json()) == 2
 
    def test_skip_parameter(self, client):
        """TC-30: ?skip=3 skips the first 3 tasks."""
        for i in range(5):
            client.post("/tasks/", json={"title": f"Task {i}"})
        r_all = client.get("/tasks/")
        r_skip = client.get("/tasks/?skip=3")
        assert len(r_skip.json()) == len(r_all.json()) - 3