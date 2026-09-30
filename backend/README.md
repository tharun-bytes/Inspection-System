# Backend API

Owns inspection records and enriches them with AI severity verdicts. Owner:
**Backend developer**.

## Run locally

```bash
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Interactive docs: <http://localhost:8000/docs>

The AI service must be running on port 8001 for predictions to resolve. Start it
first (see `ai/README.md`).

## Configuration

All settings are environment variables prefixed `INSPECTION_`, or a `.env` file.

| Variable                | Default                     | Purpose                       |
| ----------------------- | --------------------------- | ----------------------------- |
| `INSPECTION_DATABASE_URL` | `sqlite:///./inspection.db` | SQLAlchemy connection string |
| `INSPECTION_AI_SERVICE_URL` | `http://localhost:8001` | AI service base URL         |
| `INSPECTION_AI_TIMEOUT_SECONDS` | `5.0`                | AI request timeout           |
| `INSPECTION_AI_ENABLED` | `true`                      | Set false to skip AI calls    |
| `INSPECTION_CORS_ORIGINS` | `http://localhost:5173`   | Comma-separated allow-list   |

## Endpoints

| Method | Path                                | Purpose                       |
| ------ | ----------------------------------- | ----------------------------- |
| GET    | `/health`                           | DB + AI dependency status     |
| GET    | `/api/inspections`                  | List, filter, paginate        |
| POST   | `/api/inspections`                  | Create and auto-predict       |
| GET    | `/api/inspections/stats`            | Dashboard aggregates          |
| GET    | `/api/inspections/{id}`             | Fetch one                     |
| PATCH  | `/api/inspections/{id}`             | Update fields / status / notes |
| DELETE | `/api/inspections/{id}`             | Delete                        |
| POST   | `/api/inspections/{id}/reinspect`   | Re-run the AI prediction      |

Query parameters for the list endpoint: `status`, `severity`, `limit` (1-200),
`offset`.

## Behaviour worth knowing

- On create, the record is written first, then the AI service is called. If the
  call fails, the record is **still saved** with `status=pending`, `severity=null`
  and an `ai_warning` in the response. `POST /{id}/reinspect` backfills it later.
- `status` is derived from severity: `minor -> passed`, `major -> review`,
  `critical -> failed`, no verdict -> `pending`.
- `part_serial` is unique; duplicates return `409`.

## Tests

```bash
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Tests use an in-memory SQLite database and a stub AI client, so they never need
a running model service.

## Branch rules

Commit to the `backend` branch only. Never edit `ai/`, `frontend/` or
`integration/`. See `CONTRIBUTING.md` at the repo root.
