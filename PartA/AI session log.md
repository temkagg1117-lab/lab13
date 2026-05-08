# Project Decision Log — Personal Task Tracker

## LOG-001 · Project scope definition

**Огноо:** 2025-04-30
**Төлөв:** Confirmed

### Шийдвэр
Personal Task Tracker-ийн хамрах хүрээ, MVP онцлог, non-goal-уудыг тодорхойлов.

### MVP онцлог (5)
1. Task CRUD — үүсгэх, засах, устгах, дууссан гэж тэмдэглэх
2. Due date + хугацаа дууссан анхааруулга
3. Priority — Low / Medium / High
4. Labels / Tags — олон label нэмэх, label-аар шүүх
5. Search & Filter — нэрээр хайх, priority / label / status-аар шүүх

### Non-goals
- Олон хэрэглэгч, authentication
- Push / email мэдэгдэл
- Calendar sync
- Файл хавсаргах
- Давтагдах task
- Analytics / тайлан

---

## LOG-002 · Tech stack сонголт

**Огноо:** 2025-04-30
**Төлөв:** Confirmed → ADR-001 баримтжуулсан

### Харьцуулсан stack-ууд

| Stack | Дүгнэлт |
|---|---|
| Python FastAPI + SQLite | ✅ Сонгосон |
| Node.js + Express + MongoDB | ❌ Хасагдсан |
| Spring Boot + PostgreSQL | ❌ Хасагдсан |

### Шийдвэр
**Python FastAPI + SQLite** — хамгийн бага setup, автомат Swagger UI, Pydantic validation, SQLite нэг файл тул deploy хялбар.

### Шалтгаан
- Node.js: MongoDB жижиг төсөлд хэт хүнд, async callback complexity нэмнэ
- Spring Boot: Java boilerplate маш их, хувийн жижиг төсөлд overkill

### Холбоос
→ `docs/ADR-001-FastAPI-SQLite.md`

---

## LOG-003 · Architecture design

**Огноо:** 2025-04-30
**Төлөв:** Confirmed

### Шийдвэр
3 давхаргат architecture сонгов.

| Давхарга | Технологи | Үүрэг |
|---|---|---|
| API layer | FastAPI routes + Pydantic | HTTP, validation, serialization |
| Service layer | Python classes | Business logic, filter, search |
| Database layer | SQLAlchemy ORM + SQLite | CRUD, query |

### Data flow
```
Client → [Pydantic validate] → Router → Service → SQLAlchemy → SQLite
                                                              ↓
Client ← [Pydantic serialize] ← Router ← Service ←──────────┘
```

### Folder structure
```
app/
├── main.py
├── database.py
├── models/        ← ORM
├── schemas/       ← Pydantic
├── routers/       ← Endpoints
└── services/      ← Business logic
tests/
```

---

## LOG-004 · Project documentation setup

**Огноо:** 2025-04-30
**Төлөв:** Confirmed

### Үүсгэсэн баримт бичгүүд

| Файл | Зорилго |
|---|---|
| `README.md` | Setup, run, test заавар |
| `docs/ADR-001-FastAPI-SQLite.md` | Stack сонголтын шийдвэрийн бүртгэл |
| `docs/stack.md` | Stack харьцуулалт |
| `CLAUDE.md` | Build команд, code convention, no-go zone |

### Тогтоосон дүрмүүд (CLAUDE.md-аас)
- Router дотор business logic **хориотой**
- Raw SQL **хориотой** — ORM only
- Test бүр in-memory SQLite ашиглана
- Coverage хамгийн багадаа **80%** (`app/services/`)
- Нэрлэх дүрэм: файл `snake_case`, class `PascalCase`, функц `verb_noun`