# Storage Locker Management API — API Documentation

REST API for managing storage lockers in shopping malls, train stations and airports.
Customers rent a locker for a number of hours. The API tracks locker availability, calculates the price and stores rental records.

- **Base URL:** `http://localhost:8000`
- **Swagger UI:** `http://localhost:8000/docs`
- **Format:** JSON (`Content-Type: application/json`)
- **Timestamps:** UTC, ISO 8601 (e.g. `2026-10-30T07:13:09.174656Z`)
- **Money:** decimal values returned as strings with 2 decimal places (e.g. `"1500.00"`)

## Endpoints

| Method | Path                          | Description                          | Success |
|--------|-------------------------------|--------------------------------------|---------|
| GET    | `/health`                     | API and database health check        | 200     |
| GET    | `/lockers`                    | List all lockers with availability   | 200     |
| GET    | `/lockers/available`          | List available (active, free) lockers| 200     |
| GET    | `/lockers/{locker_id}`        | Get a locker by ID                   | 200     |
| POST   | `/lockers`                    | Create a locker                      | 201     |
| PUT    | `/lockers/{locker_id}`        | Update a locker                      | 200     |
| DELETE | `/lockers/{locker_id}`        | Delete a locker without rentals      | 204     |
| GET    | `/rentals`                    | List all rentals                     | 200     |
| GET    | `/rentals/{rental_id}`        | Get a rental by ID                   | 200     |
| POST   | `/rentals`                    | Rent a locker                        | 201     |
| PUT    | `/rentals/{rental_id}`        | Update the customer name             | 200     |
| POST   | `/rentals/{rental_id}/complete` | Complete an active rental          | 200     |
| DELETE | `/rentals/{rental_id}`        | Delete a COMPLETED/EXPIRED rental    | 204     |

---

## Health

### GET `/health`

Runs `SELECT 1` against PostgreSQL.

**200 OK**
```json
{ "status": "ok", "database": "connected" }
```
**503 Service Unavailable**: the database cannot be reached.
```json
{ "detail": "Database is not reachable" }
```

---

## Lockers

### Locker object

| Field          | Type    | Notes                                                    |
|----------------|---------|----------------------------------------------------------|
| `id`           | integer | Generated                                                |
| `number`       | string  | Required, unique, 1–20 characters                        |
| `size`         | string  | `SMALL`, `MEDIUM` or `LARGE`                             |
| `hourly_rate`  | decimal | Required, > 0, max 2 decimal places                      |
| `is_active`    | boolean | Default `true`. Inactive lockers cannot be rented        |
| `is_available` | boolean | **Calculated, read-only**: `is_active` and no ongoing rental |

### GET `/lockers`

**200 OK**
```json
[
  { "id": 1, "number": "A-101", "size": "MEDIUM", "hourly_rate": "500.00", "is_active": true, "is_available": false },
  { "id": 2, "number": "B-202", "size": "SMALL",  "hourly_rate": "300.00", "is_active": true, "is_available": true }
]
```

### GET `/lockers/available`

Returns only lockers where `is_available` is `true`. Same response format as `GET /lockers`.

### GET `/lockers/{locker_id}`

**200 OK**
```json
{ "id": 1, "number": "A-101", "size": "MEDIUM", "hourly_rate": "500.00", "is_active": true, "is_available": true }
```
**404 Not Found**
```json
{ "detail": "Locker 99 not found" }
```

### POST `/lockers`

**Request**
```json
{ "number": "A-101", "size": "MEDIUM", "hourly_rate": "500.00", "is_active": true }
```
**201 Created**
```json
{ "id": 1, "number": "A-101", "size": "MEDIUM", "hourly_rate": "500.00", "is_active": true, "is_available": true }
```
**409 Conflict**: the locker number already exists.
```json
{ "detail": "Locker number 'A-101' already exists" }
```
**422 Unprocessable Entity**: validation error, e.g. `{"number": "", "size": "HUGE", "hourly_rate": "0"}`:
```json
{
  "detail": [
    { "type": "string_too_short", "loc": ["body", "number"], "msg": "String should have at least 1 character", "input": "" },
    { "type": "literal_error", "loc": ["body", "size"], "msg": "Input should be 'SMALL', 'MEDIUM' or 'LARGE'", "input": "HUGE" },
    { "type": "greater_than", "loc": ["body", "hourly_rate"], "msg": "Input should be greater than 0", "input": "0" }
  ]
}
```

### PUT `/lockers/{locker_id}`

Replaces all locker fields (same body and rules as POST).

**Request**
```json
{ "number": "A-101", "size": "LARGE", "hourly_rate": "750.00", "is_active": true }
```
**200 OK**: updated locker · **404** not found · **409** number used by another locker · **422** validation error

Changing `hourly_rate` does not change the price of rentals that already exist.

### DELETE `/lockers/{locker_id}`

**204 No Content**: deleted.
**404 Not Found**
**409 Conflict**: the locker has rentals. Delete them first, or set `is_active` to `false` instead.
```json
{ "detail": "Locker has rental history and cannot be deleted" }
```

---

## Rentals

### Rental object

| Field           | Type     | Notes                                       |
|-----------------|----------|---------------------------------------------|
| `id`            | integer  | Generated                                   |
| `locker_id`     | integer  | Rented locker                               |
| `customer_name` | string   | 1–100 characters                            |
| `start_time`    | datetime | Set by server (current UTC time)            |
| `end_time`      | datetime | `start_time + duration_hours`               |
| `total_price`   | decimal  | Calculated by server                        |
| `status`        | string   | `ACTIVE`, `COMPLETED` or `EXPIRED`          |

### GET `/rentals`

**200 OK**: array of rental objects, ordered by ID.

### GET `/rentals/{rental_id}`

**200 OK**
```json
{
  "id": 1,
  "locker_id": 1,
  "customer_name": "Aisultan",
  "start_time": "2026-10-30T07:00:00.000000Z",
  "end_time": "2026-10-30T10:00:00.000000Z",
  "total_price": "1500.00",
  "status": "ACTIVE"
}
```
**404 Not Found**
```json
{ "detail": "Rental 99 not found" }
```

### POST `/rentals`

**Request**
```json
{ "locker_id": 1, "customer_name": "Aisultan", "duration_hours": 3 }
```
`duration_hours` must be an integer from 1 to 720.

**201 Created**: the rental object shown above (`status` = `ACTIVE`).

| Error | When                                    | `detail`                            |
|-------|-----------------------------------------|-------------------------------------|
| 404   | Locker does not exist                   | `Locker 99 not found`               |
| 409   | Locker has `is_active = false`          | `Locker is not active`              |
| 409   | Locker already has an ongoing rental    | `Locker is already occupied`        |
| 422   | Invalid body (e.g. `duration_hours: 0`) | Pydantic validation error list      |

### PUT `/rentals/{rental_id}`

Only the customer name can be changed. Price, status and times are managed by the server.

**Request**
```json
{ "customer_name": "Aisultan Khalelov" }
```
**200 OK**: updated rental · **404** not found · **422** validation error

### POST `/rentals/{rental_id}/complete`

Sets the status to `COMPLETED`, which releases the locker. No request body.
The price stays as paid when the rental was created.

**200 OK**: rental with `"status": "COMPLETED"`
**404 Not Found**
**409 Conflict**: the rental is not active.
```json
{ "detail": "Rental is already COMPLETED" }
```
```json
{ "detail": "Rental is already EXPIRED" }
```

### DELETE `/rentals/{rental_id}`

**204 No Content**: deleted (only `COMPLETED` or `EXPIRED` rentals).
**404 Not Found**
**409 Conflict**
```json
{ "detail": "Active rental cannot be deleted; complete it first" }
```

---

## Business rules

### Rental pricing

```
total_price = hourly_rate × duration_hours
```

The price is calculated once, when the rental is created, from the booked number of hours. Money is calculated with Python `Decimal` and stored as `NUMERIC(10, 2)`, so there are no float rounding errors.

| Hourly rate | `duration_hours` | Price   |
|-------------|------------------|---------|
| 500.00      | 1                | 500.00  |
| 500.00      | 3                | 1500.00 |
| 750.00      | 3                | 2250.00 |

### Locker availability

Availability is **not stored** in the database, so it can never get out of sync. A locker is available when:

1. `is_active` is `true`, **and**
2. it has no rental with `status = 'ACTIVE'` **and** `end_time` in the future.

A locker can have only one ongoing rental. Creating a rental locks the locker row with `SELECT … FOR UPDATE` inside a PostgreSQL transaction. If two requests try to rent the same locker at the same moment, the second one waits for the first to commit, then sees the new rental and gets `409`.

### Rental expiration

An `ACTIVE` rental whose `end_time` has passed is expired. There is no background job. Instead, the function `expire_overdue_rentals()` runs at the start of the locker and rental endpoints. It executes:

```sql
UPDATE rentals SET status = 'EXPIRED' WHERE status = 'ACTIVE' AND end_time <= now();
```

The availability check also compares `end_time` with the current time. A rental that has run out therefore never blocks a locker, even if its status has not yet been written as `EXPIRED`.

## Status codes summary

| Code | Meaning                                                    |
|------|------------------------------------------------------------|
| 200  | OK                                                         |
| 201  | Created                                                    |
| 204  | Deleted (empty body)                                       |
| 404  | Locker or rental not found                                 |
| 409  | Conflict: duplicate number, occupied/inactive locker, invalid state |
| 422  | Request validation failed                                  |
| 503  | Database not reachable (health check)                      |
