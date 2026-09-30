# Architecture

## Services

```
┌────────────┐   HTTP    ┌────────────┐   HTTP    ┌────────────┐
│  frontend  │ ────────► │  backend   │ ────────► │     ai     │
│ React/Vite │  :8000    │  FastAPI   │  :8001    │  FastAPI   │
│  :5173     │           │  SQLAlchemy│           │  sklearn   │
└────────────┘           └────────────┘           └────────────┘
                                                        │
                                                  joblib artifact
```

Each service is independently deployable and has its own dependencies, tests and
README. The frontend never calls the AI service directly, and the AI service
knows nothing about storage.

## Data flow for one inspection

1. The user fills in the form in the frontend.
2. The frontend `POST`s to `/api/inspections`.
3. The backend validates the payload (422 on failure), writes the record with
   `status=pending`, and commits — **the record is durable before the AI call**.
4. The backend `POST`s the measurements to the AI service's `/predict`.
5. The AI service normalises each measurement against its reference limit,
   appends the shift penalty, and runs the classifier.
6. The backend stores `severity` and `confidence`, derives `status`, and responds.
7. The frontend shows the verdict, or a warning if step 4 failed.

## Failure behaviour

This is the part worth being explicit about.

**AI service down or slow.** The record is still saved. `severity` and
`confidence` stay `null`, `status` stays `pending`, and the response carries an
`ai_warning` explaining what happened. The UI surfaces that warning and offers a
**Re-predict** action that calls `POST /api/inspections/{id}/reinspect` once the
service is back. Nothing is lost and nothing blocks the inspector.

**Backend down.** The frontend shows a clear "Backend unreachable" banner. The
AI service stays up and healthy on its own.

**Database down.** `/health` reports `degraded` and the record is not written.

The design rule: the AI service enriches records, it never gates them.

## The severity model

The AI service learns a weighted risk score over measurements expressed as
ratios against their reference limits:

```
score = 0.30 * dimension_deviation_pct / 5.0
      + 0.20 * surface_roughness_ra   / 3.2
      + 0.20 * torque_nm              / 45.0
      + 0.15 * vibration_mm_s         / 8.5
      + 0.10 * temperature_c          / 95.0
      + 0.05 * cycle_time_s           / 60.0
      + shift_penalty            (day 0.00, evening 0.02, night 0.05)

score >= 0.58 -> critical
score >= 0.42 -> major
else          -> minor
```

Because severity is a *linear* function of the ratios, the classifier is
multinomial logistic regression — linear decision boundaries are the right
inductive bias. A random forest was tried and rejected: axis-aligned splits
approximate the diagonal boundary poorly and made the model unstable near the
thresholds, under-calling lone severe measurements. See `ai/README.md`.

## Data model

One table, `inspections`:

| Column                   | Type    | Notes                            |
| ------------------------ | ------- | -------------------------------- |
| `id`                     | int PK  |                                  |
| `part_serial`            | str     | unique, indexed                  |
| `part_name`              | str     |                                  |
| `inspector`              | str     |                                  |
| `material`               | str     | steel/aluminum/plastic/brass/composite |
| `shift`                  | str     | day/evening/night                |
| `dimension_deviation_pct`| float   |                                  |
| `surface_roughness_ra`   | float   |                                  |
| `torque_nm`              | float   |                                  |
| `temperature_c`          | float   |                                  |
| `vibration_mm_s`         | float   |                                  |
| `cycle_time_s`           | float   |                                  |
| `severity`               | str?    | null until scored                |
| `confidence`             | float?  | null until scored                |
| `status`                 | str     | pending/passed/failed/review     |
| `notes`                  | text?   |                                  |
| `created_at`             | datetime|                                  |
| `updated_at`             | datetime|                                  |

SQLite in development via `INSPECTION_DATABASE_URL`. The SQLAlchemy models use
standard types, so moving to PostgreSQL is a URL change plus a driver install.

## Ports and configuration

| Service | Port | Key settings                                             |
| ------- | ---- | -------------------------------------------------------- |
| frontend| 5173 | `VITE_API_URL`                                            |
| backend | 8000 | `INSPECTION_DATABASE_URL`, `INSPECTION_AI_SERVICE_URL`, `INSPECTION_CORS_ORIGINS` |
| ai      | 8001 | — (trains on first start if no artifact exists)           |

## Testing strategy

| Layer          | Where            | How it runs                                        |
| -------------- | ---------------- | -------------------------------------------------- |
| Model / logic  | `ai/tests`       | `pytest` — fast, no services needed                 |
| API behaviour  | `backend/tests`  | `pytest` + in-memory SQLite + stubbed AI client     |
| UI             | `frontend/src/__tests__` | `vitest` + Testing Library, `fetch` mocked  |
| Cross-service  | `integration/tests` | `pytest` against the real running stack via compose |

The backend tests never need the model service: the AI client is injected, and
the suite substitutes a stub. That keeps the backend suite fast and independent
of the model's accuracy.
