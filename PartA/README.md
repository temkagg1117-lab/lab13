# Personal Task Tracker

A lightweight, single-user task management REST API built with **Python FastAPI** and **SQLite**. Designed for simplicity — no Docker, no external database server, no unnecessary overhead. One command to run, one file to store your data.

---

## Features

- **Task CRUD** — create, read, update, and delete tasks
- **Due dates** — set deadlines and identify overdue tasks at a glance
- **Priority levels** — mark tasks as `low`, `medium`, or `high`
- **Labels / tags** — attach multiple labels to any task for flexible organisation
- **Search & filter** — search by title, filter by priority, label, status, or due date
- **Auto-generated API docs** — interactive Swagger UI available at `/docs` with no extra setup
- **Automatic validation** — request and response validation powered by Pydantic

---

## Tech stack

| Layer    | Technology                  |
|----------|-----------------------------|
| Framework | FastAPI                    |
| Database  | SQLite (via SQLAlchemy ORM) |
| Validation | Pydantic v2               |
| Server   | Uvicorn (ASGI)              |
| Testing  | pytest + httpx              |

---

## Project structure

```
task-tracker/
├── app/
│   ├── main.py           # FastAPI app entry point
│   ├── database.py       # SQLAlchemy engine and session
│   ├── models.py         # ORM models (Task, Label)
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── routers/
│   │   ├── tasks.py      # Task endpoints
│   │   └── labels.py     # Label endpoints
│   └── services/
│       ├── task_service.py
│       ├── label_service.py
│       └── filter_service.py
├── tests/
│   ├── test_tasks.py
│   └── test_labels.py
├── tasks.db              # SQLite database file (auto-created on first run)
├── requirements.txt
└── README.md
```

---

## Setup

### Prerequisites

- Python 3.10 or higher
- `pip` package manager

### 1. Clone the repository

```bash
git clone https://github.com/your-username/task-tracker.git
cd task-tracker
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

`requirements.txt` includes:

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.0
pydantic>=2.0.0
httpx>=0.27.0
pytest>=8.0.0
```

### 4. (Optional) Configure environment variables

Create a `.env` file in the project root to override defaults:

```env
DATABASE_URL=sqlite:///./tasks.db
APP_ENV=development
```

The database file is created automatically on first run — no migration step required.

---

## Run

### Development server

```bash
uvicorn app.main:app --reload
```

The API will be available at:

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | API root |
| `http://localhost:8000/docs` | Interactive Swagger UI |
| `http://localhost:8000/redoc` | ReDoc documentation |

### Custom host / port

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

---

## API overview

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tasks` | List all tasks (supports filters) |
| `POST` | `/tasks` | Create a new task |
| `GET` | `/tasks/{id}` | Get a single task |
| `PUT` | `/tasks/{id}` | Update a task |
| `DELETE` | `/tasks/{id}` | Delete a task |

**Filter parameters for `GET /tasks`:**

```
?priority=high
?status=todo
?label=work
?due_before=2025-05-01
?q=meeting
```

### Labels

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/labels` | List all labels |
| `POST` | `/labels` | Create a new label |
| `DELETE` | `/labels/{id}` | Delete a label |

### Example request

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Write project proposal",
    "due_date": "2025-05-10",
    "priority": "high",
    "labels": ["work", "urgent"]
  }'
```

---

## Test

### Run all tests

```bash
pytest
```

### Run with verbose output

```bash
pytest -v
```

### Run a specific test file

```bash
pytest tests/test_tasks.py
```

### Run with coverage report

```bash
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

Tests use an in-memory SQLite database (`sqlite:///:memory:`) so they never touch your real `tasks.db` file.

---

## Non-goals

This project intentionally does **not** include:

- Multi-user support or authentication
- Push / email notifications
- Calendar sync (Google Calendar, iCal)
- File attachments
- Recurring tasks
- Analytics or reporting dashboards

These features are out of scope for this personal, single-user tool. See [ADR-001](./docs/ADR-001-FastAPI-SQLite.md) for the full architecture decision record.

---

## License

MIT — see [LICENSE](./LICENSE) for details.