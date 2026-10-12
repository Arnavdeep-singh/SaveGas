# SaveGas

# ⛽ Gas Timing

A gas price tracking app focused on **when to fill up**.

The app will track historical gas prices and analyze patterns to identify when prices are typically lower. Users will also be able to select gas stations they frequent and receive an alert when the price drops to an unusually low level compared to its recent history.

### Planned Features

* Historical gas price tracking
* Identify day/time patterns in gas prices
* Personal gas station watchlists
* Alerts for unusually low prices
* Price history and statistics
* Potentially personalized price predictions

### Tech Stack

Currently planning to use:

* **Frontend:** React + TypeScript
* **Backend:** Python + FastAPI
* **Database:** PostgreSQL
* **Analysis:** Python, Pandas, NumPy, SciPy

The stack and features may change as development progresses.

> 🚧 **Currently in early development**

## Run the current station milestone

PostgreSQL runs in Docker; FastAPI and Vite run on the host. Docker publishes
PostgreSQL on **127.0.0.1:5433**, avoiding the Windows PostgreSQL instance on 5432.
The Compose credentials are local development defaults only.

From the project root:

```powershell
docker compose up -d postgres
Copy-Item backend/.env.example backend/.env # only if .env does not already exist
cd backend
uv sync
uv run alembic upgrade head
uv run python -m uvicorn main:app --reload
```

In a second terminal:

```powershell
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173 for the station list, or http://127.0.0.1:8000/docs
to create a station interactively. The list shows loading, empty, timeout, and
error states, with retry after failure. Refresh the page after adding a station.
`VITE_API_BASE_URL` optionally changes the API address; see `frontend/.env.example`.
Vite variables are public browser configuration, so never put secrets in them.

### API contract

`GET /api/stations` returns a JSON array in ascending ID order, or `[]` when empty.
`POST /api/stations` returns HTTP **201** with the saved station and generated ID.
Example request:

```json
{"name":"Shell Kingsway","brand":"Shell","latitude":49.232,"longitude":-123.023}
```

Names/brands are trimmed, required, and limited to 100 characters. Latitude must
be between -90 and 90; longitude between -180 and 180. Nonfinite coordinates and
unexpected fields are rejected. Invalid requests return **422**. Database errors
return **503** without exposing connection details. Station IDs are assigned by
the database. Duplicate station entries are currently allowed: names alone do
not uniquely identify a physical station, and deduplication needs a defined rule.

### How one request works

1. React's `useEffect` fetches the stations when the component mounts. It checks
   HTTP status because `fetch` does not reject on a 503 response. Cleanup aborts
   the request and ignores late results, including React StrictMode's dev remount.
2. `main.py` configures FastAPI/CORS and includes `routers/stations.py`. Keeping
   station HTTP handlers in a router avoids growing one large application file.
3. For POST, `schemas.py` defines `StationCreate`, the input contract. Pydantic
   validates the body before the handler runs. `StationResponse` controls output;
   `from_attributes=True` lets it read fields directly from SQLAlchemy objects.
4. `Depends(get_db)` calls the session dependency in `database.py`. Each request
   gets its own session: a unit of work that tracks ORM objects and manages a
   transaction. The engine/pool is shared, but mutable sessions are not. The
   dependency closes the session even if the request fails.
5. `models.py` describes the persisted table. POST adds an object, commits its
   INSERT, and refreshes it to read the database-generated ID. Failed writes roll
   back. GET uses SQLAlchemy's `select(Station)` and returns the ordered rows.
6. FastAPI serializes the ORM rows through `StationResponse` into JSON. React
   stores the array in state and renders each station using its ID as the key.

The ORM model and Pydantic schemas serve different purposes: database structure
versus HTTP validation/serialization. API validation does not enforce coordinate
ranges for direct SQL writes; the first migration intentionally preserves the
existing database structure. No service/repository layer is added yet because
these handlers have only simple persistence logic.

### Migrations

Application startup no longer calls `create_all`. Alembic owns schema changes.
`migrations/versions/0001_create_stations.py` creates the original five-column
table on a new database. `migrations/env.py` uses the same configured engine and
model metadata as the application, without duplicating credentials in alembic.ini.

The existing local table was compared against model metadata and then stamped
as `0001`, preserving it. **Stamping records a revision; it does not run SQL.**
For another existing database, verify its schema matches this migration before
running `uv run alembic stamp 0001`. For a fresh database use `upgrade head`.
Never stamp an unverified schema merely to bypass a migration error.

For future model changes, from `backend`:

```powershell
uv run alembic revision --autogenerate -m "describe the schema change"
# Review the generated migration before applying it.
uv run alembic upgrade head
uv run alembic check
uv run alembic current
```

The initial downgrade drops stations and its data; use downgrade only deliberately.
Changing Compose passwords does not reset credentials in an existing data volume.

### Tests

From `backend`:

```powershell
uv run pytest
# Also verify real PostgreSQL and migration upgrade/downgrade:
$env:RUN_POSTGRES_TESTS = "1"
uv run pytest
```

The default API tests override `get_db` with a fresh in-memory SQLite database per
test. They cover creation, retrieval, ordering, validation, rollback/error responses,
health, and CORS without modifying development data. SQLite alone cannot verify
PostgreSQL behavior, so the opt-in integration test creates a unique PostgreSQL
schema inside a transaction, runs migrations and both endpoints there, and rolls
everything back. It uses session savepoints so endpoint commits cannot commit
the outer test transaction. The configured PostgreSQL user needs CREATE SCHEMA.

From `frontend`, run `npm run build` and `npm run lint`.

