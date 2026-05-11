# F.CSM311 — AI-Assisted Software Construction

## Төслийн нэр
Personal Task Tracker API

## Төслийн зорилго
Энэхүү төсөл нь AI-assisted software construction workflow-г практикт хэрэгжүүлэх зорилготой жижиг task management API систем юм.

## Үндсэн боломжууд

- Task CRUD
- Due date validation
- Priority system
- Label/tag support
- Search болон filter

## Ашигласан технологи

- FastAPI
- SQLite
- SQLAlchemy
- Pytest

## Төслийн бүтэц

- partA → Төлөвлөлт ба архитектур
- partB → Хэрэгжилт
- partC → Эргэцүүлэл ба AI usage report

## Ажиллуулах

```bash
uvicorn partB.src.main:app --reload