# Space Bounty Hunters API

A REST API for space bounty hunters: a database of wanted criminals and a journal of their own bounty hunting attempts.

Web Application Development, Endterm assignment. There is no frontend: use Postman or Swagger UI.

## Tech stack

Python 3.12 · FastAPI · SQLAlchemy 2.0 · Pydantic · PostgreSQL 16 · psycopg2 · Uvicorn · Docker Compose

## Project structure

```
Bounty_Hunters/
├── app/
│   ├── main.py            # FastAPI app, /health
│   ├── database.py        # engine, session, Base, get_db dependency
│   ├── models.py          # WantedCriminal and HuntLog tables (one-to-many)
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── crud.py            # database queries, filters, sorting
│   └── routers/
│       ├── criminals.py   # /api/criminals/ endpoints
│       └── hunts.py       # /api/hunts/ endpoints (CRUD)
├── db/
│   └── init.sql           # schema + seed data (6 criminals, 10 hunt logs)
├── postman/
│   └── Space_Bounty_Hunters_API.postman_collection.json
├── compose.yaml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Run

Requirements: Docker Desktop.

```bash
cd Bounty_Hunters
cp .env.example .env
docker compose up --build
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Database setup / import

The database is created and filled **automatically**. On the first start, PostgreSQL runs [db/init.sql](db/init.sql) (mounted into `/docker-entrypoint-initdb.d/`). It creates both tables and imports 6 criminals and 10 hunt logs.

The script only runs when the database volume is empty. To reset the data to the initial state:

```bash
docker compose down -v
docker compose up --build
```

Manual import into an existing PostgreSQL database:

```bash
psql -U bounty_user -d bounty_db -f db/init.sql
# or, with the containers running:
docker compose exec -T db psql -U bounty_user -d bounty_db < db/init.sql
```

## Database models

**WantedCriminal** (`wanted_criminals`)

| Field | Type | Notes |
|---|---|---|
| id | serial PK | |
| name | varchar, nullable | real name, `null` if unknown |
| nickname | varchar | alias |
| reward | integer | bounty amount, ≥ 0 |
| latitude, longitude | float, nullable | last known coordinates |
| location_note | text, nullable | text note when exact coordinates are unknown |
| difficulty | integer | 1 to 10 |
| armed, has_crew, escape_master | boolean | |

In API responses the location is returned as one object:

```json
"last_known_location": {
  "coordinates": { "latitude": 43.2389, "longitude": 76.8897 },
  "note": null
}
```

**HuntLog** (`hunt_logs`)

| Field | Type | Notes |
|---|---|---|
| id | serial PK | |
| criminal_id | FK → wanted_criminals.id | required, must exist |
| success | boolean | was the criminal captured |
| notes | text | encounter description |
| created_at | timestamptz | set by the server (`DEFAULT NOW()`), never by the client |

Relationship: one `WantedCriminal` has many `HuntLog` records (`WantedCriminal.hunts` ↔ `HuntLog.criminal`).

## Endpoints

### Wanted Criminals

| Method | URL | Description |
|---|---|---|
| GET | `/api/criminals/` | List criminals |
| GET | `/api/criminals/{id}/` | One criminal with its hunt logs |

Query parameters for the list (all optional, they work together):

- `min_reward`, `max_reward` — reward range
- `armed`, `has_crew`, `escape_master` — `true` / `false`
- `sort` — `reward` (ascending) or `-reward` (descending)

Example: `GET /api/criminals/?min_reward=5000&armed=true&sort=-reward`

### Hunt Logs (journal)

| Method | URL | Description |
|---|---|---|
| GET | `/api/hunts/` | List hunt logs (`?criminal_id=5` to filter) |
| GET | `/api/hunts/{id}/` | One hunt log |
| POST | `/api/hunts/` | Record a capture attempt |
| PATCH | `/api/hunts/{id}/` | Update `success` and/or `notes` |
| DELETE | `/api/hunts/{id}/` | Delete a hunt log |

POST body:

```json
{
  "criminal_id": 3,
  "success": false,
  "notes": "Target escaped through an asteroid field."
}
```

## Status codes and validation

| Code | When |
|---|---|
| 200 | OK |
| 201 | Hunt log created |
| 204 | Hunt log deleted |
| 400 | `min_reward > max_reward`; PATCH body without `success` or `notes` |
| 404 | Criminal or hunt log not found; POST with a `criminal_id` that does not exist |
| 422 | Invalid data: missing fields, wrong types, non-numeric ID, unknown `sort` value, extra fields such as `created_at` in the body |

## Postman Collection

Import [postman/Space_Bounty_Hunters_API.postman_collection.json](postman/Space_Bounty_Hunters_API.postman_collection.json) into Postman. The `baseUrl` variable is `http://localhost:8000`.

- **Wanted Criminals**: listing, filtering, sorting, details, invalid requests
- **Hunt Logs**: create → read → update → delete. The create request saves the new ID into the `huntId` variable, so run the requests in order (or use the Collection Runner). Also includes invalid requests.

Each request has a test that checks the expected status code.
