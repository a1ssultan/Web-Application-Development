# Storage Locker Management API

A REST API for managing storage lockers in shopping malls, train stations and airports. Customers rent a locker for a number of hours. The API tracks which lockers are free, calculates the rental price and keeps rental records.

Web Application Development, Midterm Project (Part 1). There is no frontend: use Postman or Swagger UI.

## Features

- CRUD for **lockers** and **rentals**
- Availability is calculated from active rentals, never stored separately
- Automatic price: `hourly_rate × duration_hours`
- No double booking: PostgreSQL transaction + row lock (`SELECT … FOR UPDATE`)
- Rentals expire automatically (checked on each relevant request)
- Validation and clear error messages (404 / 409 / 422)
- Swagger UI, a manual [API documentation](API_DOCUMENTATION.md) and a ready-to-run [Postman Collection](postman/Storage_Locker_API.postman_collection.json)
- Fully containerized: starts with `docker compose up`

## Tech stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 (sync) · Pydantic · PostgreSQL 16 · psycopg2 · Uvicorn · Docker · Docker Compose

## Architecture

```
 Postman / Browser (Swagger UI)
            │  http://localhost:8000
            ▼
 ┌──────────────────────────┐
 │ backend                  │  built from ./Dockerfile
 │ FastAPI + Uvicorn :8000  │  ports: "8000:8000"
 └────────────┬─────────────┘
              │  DATABASE_URL = postgresql+psycopg2://…@db:5432/locker_db
              │  network: locker_network
 ┌────────────▼─────────────┐
 │ db                       │  image: postgres:16-alpine
 │ PostgreSQL :5432         │  not published to the host
 └────────────┬─────────────┘
              ▼
   postgres_data (named volume)
```

Inside the backend, a request goes **router** (`app/routers/*.py`: HTTP, validation, status codes) → **crud** (`app/crud.py`: queries and business logic) → **models** (`app/models.py`: SQLAlchemy tables) → PostgreSQL.

## Project structure

```
Midterm/
├── app/
│   ├── main.py            # FastAPI app, creates tables on startup, /health
│   ├── database.py        # engine, session, Base, get_db dependency
│   ├── models.py          # Locker and Rental tables
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── crud.py            # database operations, pricing, availability, expiration
│   └── routers/
│       ├── lockers.py     # /lockers endpoints
│       └── rentals.py     # /rentals endpoints
├── postman/
│   └── Storage_Locker_API.postman_collection.json
├── .dockerignore
├── .gitignore
├── .env.example           # template (committed)
├── .env                   # real values (NOT committed, submitted as ZIP)
├── Dockerfile
├── compose.yaml
├── requirements.txt
├── API_DOCUMENTATION.md
└── README.md
```

## Environment configuration

| Variable            | Used by          | Value in `.env.example`                                              |
|---------------------|------------------|----------------------------------------------------------------------|
| `POSTGRES_DB`       | db               | `locker_db`                                                          |
| `POSTGRES_USER`     | db               | `locker_user`                                                        |
| `POSTGRES_PASSWORD` | db               | `locker_pass`                                                        |
| `DATABASE_URL`      | backend          | `postgresql+psycopg2://locker_user:locker_pass@db:5432/locker_db`    |

Docker Compose reads `.env` automatically and substitutes the `${...}` values in `compose.yaml`. The Python code only reads `DATABASE_URL` (`app/database.py`), so there are no credentials in the source code.

These are **development-only** credentials. `.env` is listed in `.gitignore`. Only `.env.example` is in the repository, and the working `.env` is submitted separately as a ZIP file.

If you change the user, password or database name, update `DATABASE_URL` to match.

## Installation and startup (Docker Desktop on macOS)

1. Install and start **Docker Desktop**. Python and PostgreSQL are **not** needed on your machine.
2. Open a terminal in the project folder.
3. Make sure `.env` exists. If not, create it: `cp .env.example .env`
4. Start everything:

```bash
docker compose up
```

The first run builds the backend image. Compose then starts `db`, waits until its healthcheck passes, and starts `backend`. The tables are created automatically on startup.

After you change the code, rebuild with `docker compose up --build`.

## Swagger UI

- Swagger UI: **http://localhost:8000/docs**
- OpenAPI JSON: http://localhost:8000/openapi.json
- Health check: http://localhost:8000/health

## Postman Collection

1. Open Postman → **Import** → choose `postman/Storage_Locker_API.postman_collection.json`.
2. The collection variable `base_url` is `http://localhost:8000`.
3. Run the requests from top to bottom, or click **Run collection**.
   - *Create locker* saves `locker_id` and *Create rental* saves `rental_id`. The later requests reuse them, so no IDs are hardcoded.
   - The numbered requests (1–15) are the main workflow. The un-numbered ones show error cases (404, 409, 422).
   - Every request has tests that you can see in the **Test Results** tab.

## Example workflow

```bash
# 1. Create a locker
curl -X POST http://localhost:8000/lockers -H "Content-Type: application/json" \
  -d '{"number": "A-101", "size": "MEDIUM", "hourly_rate": "500.00"}'

# 2. Rent it for 3 hours → total_price = 500.00 × 3 = 1500.00
curl -X POST http://localhost:8000/rentals -H "Content-Type: application/json" \
  -d '{"locker_id": 1, "customer_name": "Aisultan", "duration_hours": 3}'

# 3. Locker is now occupied → not in this list; renting it again returns 409
curl http://localhost:8000/lockers/available

# 4. Complete the rental → locker is available again
curl -X POST http://localhost:8000/rentals/1/complete
```

## Database persistence

PostgreSQL stores its files in `/var/lib/postgresql/data`. That folder is mounted from the **named volume** `postgres_data`, which Docker shows as `midterm_postgres_data`. The volume lives outside the container, so the data survives when containers are stopped, removed or recreated.

To check:

1. Create a locker.
2. Run `docker compose down`.
3. Run `docker compose up`.
4. `GET /lockers` still returns the locker.

## Docker networking

Both services join the bridge network `locker_network`. Docker has a built-in DNS on that network, so the backend reaches PostgreSQL by the **service name** `db` (`@db:5432` in `DATABASE_URL`). Inside the backend container, `localhost` would point to the backend container itself.

Only the backend publishes a port (`8000:8000`, which means host port 8000 → container port 8000). The database port 5432 is reachable only inside the Docker network.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Cannot connect to the Docker daemon` | Start Docker Desktop and wait until it is running. |
| `port is already allocated` (8000) | Another app uses port 8000. Stop it (`lsof -i :8000`), or change the mapping to `"8001:8000"` and use `http://localhost:8001`. |
| Backend logs `password authentication failed` | The volume was created with different credentials. Run `docker compose down -v` and then `docker compose up` (this deletes the data). |
| Code changes are not visible | Run `docker compose up --build`. |
| Postman `Could not get response` | Check `docker compose ps`, and check that `base_url` is `http://localhost:8000`. |
| `409 Locker is already occupied` | Complete the existing rental first (`POST /rentals/{id}/complete`). |
| See what is happening | `docker compose logs -f backend` or `docker compose logs -f db` |
| Look inside the database | `docker compose exec db psql -U locker_user -d locker_db -c "SELECT * FROM rentals;"` |

## Stop and reset

```bash
docker compose down      # stop and remove containers + network; the volume (data) is kept
docker compose down -v   # also remove the named volume → ALL database data is deleted
```

Use `down` for a normal stop. Use `down -v` only for a completely clean database, for example after changing the credentials or the table structure. The tables are created again on the next `docker compose up`.
