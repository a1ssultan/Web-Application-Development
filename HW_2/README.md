# Expense Tracker API 🧾

A simple but useful **multi-container application** for recording personal spending and viewing totals by category.

**Tech stack:** Python 3.12, FastAPI, PostgreSQL 16, SQLAlchemy, Docker, Docker Compose.

## Features

- Add an expense (title, category, amount in KZT, date).
- List expenses or filter by category.
- Calculate total spending and transaction count **by category** using SQL `GROUP BY`.
- View an expense by ID, or delete it.
- Read and write real records in PostgreSQL.
- Persistent database storage using a Docker **named volume**.
- Interactive API documentation at `/docs`.

## Architecture

```
Browser / Swagger / curl
         |
         v  localhost:8000
+-----------------------+
| backend: FastAPI      |
| custom Dockerfile     |
+-----------------------+
         |  db:5432 (private Docker network)
         v
+-----------------------+
| db: PostgreSQL 16     |
+-----------------------+
         |
         v
  postgres_data (named volume)
```

## Run on macOS (Docker Desktop required)

1. Install and start Docker Desktop.
2. Create your **private** `.env` (never commit it):

   ```bash
   cp .env.example .env
   ```

3. Open `.env` and replace `POSTGRES_PASSWORD` with a strong **alphanumeric** password of your own. If you use a port other than 8000, adjust `APP_PORT`.
4. Build and run **both** containers with one command:

   ```bash
   docker compose up --build -d
   ```

5. Visit http://localhost:8000/docs (Swagger UI). Confirm the database connection at http://localhost:8000/health.

The `expenses` table is created automatically on startup. PostgreSQL is not exposed outside the Compose network.

### Example API requests

**Create an expense** (writes to PostgreSQL):

```bash
curl -X POST http://localhost:8000/expenses \
  -H 'Content-Type: application/json' \
  -d '{"title":"Coffee","category":"Food","amount":"1500.00","spent_on":"2026-10-21"}'
```

**Add another:**

```bash
curl -X POST http://localhost:8000/expenses \
  -H 'Content-Type: application/json' \
  -d '{"title":"Taxi","category":"Transport","amount":"2500.00","spent_on":"2026-10-21"}'
```

**Read stored expenses:**

```bash
curl http://localhost:8000/expenses
```

**Read spending summary:**

```bash
curl http://localhost:8000/expenses/summary
```

**Filter by category:**

```bash
curl 'http://localhost:8000/expenses?category=Food'
```

**Delete an expense:**

```bash
curl -X DELETE http://localhost:8000/expenses/1
```

### Persistence demonstration for defense

1. Create a record through Swagger UI or curl.
2. Run `docker compose down` (stops and **removes containers**, but retains the named volume).
3. Run `docker compose up -d`.
4. Run `curl http://localhost:8000/expenses` again: the previous record is still there.

**Warning:** `docker compose down -v` removes the named database volume and its data. Do not use `-v` for the persistence demonstration.

### Useful commands

```bash
docker compose ps                 # container statuses
docker compose logs -f backend    # backend logs
docker compose logs -f db         # database logs
docker compose down               # remove containers, keep data
docker compose up --build         # run with live logs
```

## File structure

```
expense-tracker-api/
├── app/
│   ├── __init__.py
│   └── main.py
├── compose.yaml
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
├── .dockerignore
└── README.md
```

## Submission checklist

- [ ] Public GitHub repository has the app code, Dockerfile, compose.yaml, `.env.example`, README.
- [ ] `.env` is **not** in GitHub (`.gitignore` already excludes it).
- [ ] Upload your actual `.env` **only** as a separate attachment in the homework submission, as requested by your instructor.
- [ ] Confirm `docker compose up --build` succeeds, CRUD works, and data survives `down` / `up`.
- [ ] Press **Turn in**.

> Educational note: The app uses automatic schema creation for simplicity. A production app would typically use migration tooling (such as Alembic), stronger secrets management, and authentication.
