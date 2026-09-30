# Inspection System

Quality inspection with AI-assisted severity grading. An inspector records
measurements for a part; a model grades the defect severity as `minor`, `major`
or `critical`, and the backend turns that into a pass / review / fail decision.

Built by a team of five working in parallel across three components, using a
staged branch workflow. See [CONTRIBUTING.md](CONTRIBUTING.md) for who owns what
and [docs/WORKFLOW.md](docs/WORKFLOW.md) for the merge order.

## Architecture

```
┌────────────┐   HTTP    ┌────────────┐   HTTP    ┌────────────┐
│  frontend  │ ────────► │  backend   │ ────────► │     ai     │
│ React/Vite │  :8000    │  FastAPI   │  :8001    │  FastAPI   │
│  :5173     │           │  SQLAlchemy│           │  sklearn   │
└────────────┘           └────────────┘           └────────────┘
```

The frontend never calls the AI service. The backend is the only thing that
does, and it treats the AI service as optional: if it is down, records are still
saved unscored and can be graded later.

More detail in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick start

The whole stack, with Docker:

```bash
cd integration
docker compose up -d --build --wait
```

| Service    | URL                          |
| ---------- | ---------------------------- |
| Frontend   | <http://localhost:5173>      |
| Backend    | <http://localhost:8000/docs> |
| AI service | <http://localhost:8001/docs> |

Tear down with `docker compose down -v`.

### Running the services individually

Terminal 1 — the AI service (trains a model on first start, takes a few seconds):

```bash
cd ai
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
```

Terminal 2 — the backend:

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

Terminal 3 — the frontend:

```bash
cd frontend
npm install
npm run dev
```

The AI service must be up before the backend, or the backend will report
`ai_service: down` in `/health` and save records unscored.

## Repository layout

```
ai/           severity model + prediction service   (Preethi)
backend/      inspection record API                 (Upasana, Ramya)
frontend/     React dashboard                       (Tharun)
integration/  docker-compose, e2e suite, contracts  (Yashwanth)
docs/         architecture, workflow, test plan
CONTRIBUTING.md   team roles, branch rules, merge order
DEMO.md           the presentation runbook
```

Each service has its own README with the detail.

## API at a glance

| Method | Path                              | Service  |
| ------ | --------------------------------- | -------- |
| POST   | `/predict`                        | ai       |
| POST   | `/train`                          | ai       |
| GET    | `/health`                         | both     |
| POST   | `/api/inspections`                | backend  |
| GET    | `/api/inspections`                | backend  |
| GET    | `/api/inspections/stats`          | backend  |
| PATCH  | `/api/inspections/{id}`           | backend  |
| DELETE | `/api/inspections/{id}`           | backend  |
| POST   | `/api/inspections/{id}/reinspect` | backend  |

## Tests

| Suite      | Command                            | Checks |
| ---------- | ---------------------------------- | ------ |
| AI         | `cd ai && pytest -q`               | 31     |
| Backend    | `cd backend && pytest -q`          | 33     |
| Frontend   | `cd frontend && npm test`          | 33     |
| End-to-end | `cd integration && pytest`         | 9      |

The end-to-end suite needs the stack running. Lint is `ruff check .` in `ai/` and
`backend/`, and `npm run lint` in `frontend/`.

## The model in one paragraph

Each measurement is normalised against its reference limit, and severity comes
from a weighted sum of those ratios plus a shift penalty, thresholded at 0.42
and 0.58. Because the target is a linear function of the ratios, the classifier
is multinomial logistic regression. A random forest was tried first and
rejected: it was less accurate (87% vs 99%) and unstable near the thresholds,
under-calling a lone severe measurement. Details in
[ai/README.md](ai/README.md).
