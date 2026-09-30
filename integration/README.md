# Integration

Everything that spans more than one service. Owner: **Yashwanth**.

## Run the whole stack with Docker

```bash
cd integration
docker compose up -d --build --wait
```

| Service    | URL                            |
| ---------- | ------------------------------ |
| Frontend   | <http://localhost:5173>        |
| Backend    | <http://localhost:8000/docs>   |
| AI service | <http://localhost:8001/docs>   |

Tear down with `docker compose down -v` (the `-v` also clears the database
volume).

## Run the end-to-end tests

With the stack already running:

```bash
cd integration
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest
```

Set `SKIP_E2E=1` to skip the suite, and `E2E_AI_URL` / `E2E_API_URL` to point at
a stack running somewhere other than localhost.

## What the e2e suite covers

- both services report healthy
- a clean inspection is graded `minor` and marked `passed`
- a badly out-of-spec inspection is graded `critical` and marked `failed`
- duplicate serials are rejected with `409`
- filtering and the stats endpoint agree with each other
- re-running a prediction is idempotent
- out-of-range payloads are rejected with `422`
- records can be deleted and then return `404`

## Contract between the services

The backend is the only thing that talks to the AI service. The frontend only
ever talks to the backend.

```
frontend --HTTP--> backend --HTTP--> ai
```

The payload the backend sends to `POST /predict` on the AI service is the record
with the identifying fields removed:

```json
{
  "material": "steel",
  "shift": "day",
  "dimension_deviation_pct": 1.2,
  "surface_roughness_ra": 0.8,
  "torque_nm": 20.0,
  "temperature_c": 35.0,
  "vibration_mm_s": 1.1,
  "cycle_time_s": 15.0
}
```

The AI service answers with `severity`, `confidence` and `model_version`. The
backend maps severity to a record status: `minor -> passed`, `major -> review`,
`critical -> failed`, no verdict -> `pending`.

**If you rename a field in one service, change it in all three and re-run the
e2e suite before opening a PR.**

## Branch rules

The `integration` branch is the meeting point. Merges from `ai`, `backend` and
`frontend` land here first; see `CONTRIBUTING.md`.
