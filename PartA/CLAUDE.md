# CLAUDE.md — Personal Task Tracker

## Build commands

```bash
# Install dependencies
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run dev server
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Lint
ruff check app/
ruff format app/
```

---

## Project layout

```
app/
├── main.py          # App entry point — only router includes here
├── database.py      # Engine + SessionLocal + get_db()
├── dependencies.py  # Shared FastAPI dependencies
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic request / response schemas
├── routers/         # FastAPI APIRouter — one file per resource
└── services/        # Business logic — one file per resource
tests/
├── conftest.py      # In-memory DB setup, TestClient fixture
├── test_tasks.py
└── test_labels.py
```

---

## Code conventions

### Layer responsibilities

| Layer | Allowed | Not allowed |
|---|---|---|
| `routers/` | Parse request, call service, return response | DB queries, business logic |
| `services/` | Business logic, validation rules, DB calls | HTTP concerns, status codes |
| `models/` | Table definition, relationships | Validation, logic |
| `schemas/` | Input/output shape, field validation | DB access |

### Schemas — always use separate classes

```python
# correct
class TaskCreate(BaseModel): ...   # input
class TaskOut(BaseModel): ...      # output

# wrong — never expose ORM model directly
return db_task  # ← never do this
```

### Dependency injection — always use get_db()

```python
# correct
def get_tasks(db: Session = Depends(get_db)): ...

# wrong — never instantiate session manually inside a route
db = SessionLocal()  # ← never do this in routers
```

### Services — always receive db as first argument

```python
# correct
def create_task(db: Session, data: TaskCreate) -> Task: ...

# wrong
def create_task(data: TaskCreate) -> Task:
    db = SessionLocal()  # ← never
```

---

## Naming rules

| Thing | Convention | Example |
|---|---|---|
| Files | `snake_case.py` | `task_service.py` |
| ORM model class | `PascalCase` | `Task`, `Label` |
| Pydantic schema | `PascalCase` + suffix | `TaskCreate`, `TaskOut` |
| Service function | `verb_noun` | `create_task`, `get_task_by_id` |
| Router variable | `router` | `router = APIRouter()` |
| DB table name | `snake_case` plural | `tasks`, `labels` |
| Enum values | `lowercase` | `"low"`, `"medium"`, `"high"` |
| Test function | `test_verb_noun_condition` | `test_create_task_missing_title` |

---

## No-go zones

```python
# 1. No business logic in routers
@router.post("/tasks")
def create(data: TaskCreate, db=Depends(get_db)):
    if data.due_date < date.today():   # ← move this to service
        raise HTTPException(...)

# 2. No raw SQL — use ORM only
db.execute("SELECT * FROM tasks")     # ← never

# 3. No mutable default arguments
def create_task(tags: list = []):     # ← use Optional[list] = None

# 4. No global state
tasks_cache = {}                      # ← not allowed outside tests

# 5. No print() for logging
print("task created")                 # ← use Python logging module

# 6. Never commit sessions in services — let the router or a context manager handle it
db.commit()                           # ← only in service, never in router
```

---

## Testing rules

- All tests use **in-memory SQLite** — never touch `tasks.db`
- Each test gets a **fresh DB** via `conftest.py` fixture
- Test files mirror source: `app/routers/tasks.py` → `tests/test_tasks.py`
- Use `TestClient` from `fastapi.testclient` — no live server needed
- Cover at minimum: happy path, missing field, not-found (404)

```python
# conftest.py pattern
@pytest.fixture
def client():
    engine = create_engine("sqlite:///:memory:", ...)
    Base.metadata.create_all(engine)
    app.dependency_overrides[get_db] = lambda: SessionLocal()
    yield TestClient(app)
    Base.metadata.drop_all(engine)
```

Minimum coverage target: **80%** on `app/services/`.

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./tasks.db` | DB connection string |
| `APP_ENV` | `development` | `development` or `production` |

Never hardcode these values — always read from `.env` via `python-dotenv`.

---

## Dependencies (key packages)

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn[standard]` | ASGI server |
| `sqlalchemy` | ORM |
| `pydantic>=2` | Validation |
| `pytest` + `httpx` | Testing |
| `ruff` | Lint + format |
| `python-dotenv` | Env config |