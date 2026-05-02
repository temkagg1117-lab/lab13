# ADR-001: FastAPI + SQLite for Personal Task Tracker

## Metadata

| Field      | Value                    |
|------------|--------------------------|
| ADR Number | ADR-001                  |
| Date       | 2025-04-30               |
| Status     | Accepted                 |
| Decider    | Engineering Team         |
| Project    | Personal Task Tracker    |

---

## Context

Бид хувийн Task Tracker вэб апп хөгжүүлж байна. Энэ нь нэг хэрэглэгчид зориулсан жижиг төсөл бөгөөд дараах хязгаарлалтуудтай:

- Нэг хөгжүүлэгч, богино хугацааны MVP
- Олон хэрэглэгч, concurrency шаардлагагүй
- Дата загвар энгийн, relational (task, label, priority)
- Суурилуулалт хялбар байх ёстой — Docker, тусдаа DB server хэрэггүй
- Хурдан ажилладаг API, автомат validation шаардлагатай

---

## Decision

**Python FastAPI + SQLite** ашиглахаар шийдвэрлэв.

### FastAPI сонгосон шалтгаан

- Boilerplate код маш бага — 50 мөрөнд бүрэн REST API бичиж болно
- Pydantic-аар автомат request/response validation
- `/docs` хаягт Swagger UI автоматаар үүсдэг
- Async-first дизайн
- Python өргөн мэддэг тул contributor-д хялбар

### SQLite сонгосон шалтгаан

- Нэг `.db` файл — server, тохиргоо шаардахгүй
- Нэг хэрэглэгчийн ачааллыг бүрэн даана
- SQLAlchemy ORM-тэй нийцдэг → PostgreSQL руу шилжих хялбар
- Development орчинд Docker хэрэггүй болно

---

## Alternatives Considered

| Stack                        | Learning Curve | Dev Speed | Small Project Fit | Decision     |
|------------------------------|----------------|-----------|-------------------|--------------|
| **Python FastAPI + SQLite**  | Low            | Fast      | Excellent         | ✅ Selected  |
| Node.js + Express + MongoDB  | Medium         | Medium    | Good              | ❌ Rejected  |
| Spring Boot + PostgreSQL     | High           | Slow      | Overkill          | ❌ Rejected  |

### Node.js + Express + MongoDB — яагаад хаясан

MongoDB schema-less байдал нь бүтэцтэй relational өгөгдөлд тохиромжгүй. npm dependency overhead их, Express-ийн async callback pattern цаг шаардана.

### Spring Boot + PostgreSQL — яагаад хаясан

Java/Spring boilerplate маш их, жижиг endpoint-д ч хэт хүнд. PostgreSQL тусдаа server шаарддаг тул setup нэмэлт ажил болно. Enterprise төсөлд тохиромжтой, энэ хэрэглээнд хэтэрхий том.

---

## Consequences

### Эерэг үр дагавар

- Setup хамгийн хялбар — `.db` файл болон нэг Python процесс
- Swagger UI автоматаар үүсдэг тул API тест хялбар
- Pydantic validation — runtime алдааг эрт илрүүлнэ
- Deployment энгийн (Railway, Render, локал машин)

### Эрсдэл / Сөрөг үр дагавар

- SQLite concurrent write дэмждэггүй — олон хэрэглэгчид тохиромжгүй
- Horizontal scaling хязгаарлагдмал
- Python async/await pattern шинэ байж болно
- Өргөтгөсөн тохиолдолд PostgreSQL руу migration хийх шаардлага гарна

### Migration замнал

SQLAlchemy ORM ашигласан тул хожим PostgreSQL руу шилжихэд зөвхөн connection string өөрчлөн, schema migration ажиллуулахад хангалттай. Application logic өөрчлөгдөхгүй.

---

## Status

**Accepted** — 2025-04-30-нд батлагдав.

Төслийн хүрээ өргөжин олон хэрэглэгч эсвэл өндөр ачаалал шаардлагатай болбол энэ шийдвэрийг дахин хянана.

---

*ADR-001 | Personal Task Tracker | 2025-04-30*