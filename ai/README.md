# AI Service

Predicts defect severity (`minor` / `major` / `critical`) from inspection
measurements. Owner: **AI developer**.

## Run locally

```bash
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

Interactive docs: <http://localhost:8001/docs>

## Endpoints

| Method | Path             | Purpose                                   |
| ------ | ---------------- | ----------------------------------------- |
| GET    | `/health`        | Liveness + whether a model is loaded      |
| POST   | `/predict`       | Predict severity for one measurement      |
| POST   | `/predict/batch` | Predict for up to 500 measurements        |
| POST   | `/train`         | Retrain and persist the model             |

## How the model works

`app/data.py` generates a synthetic dataset by sampling each measurement
log-normally around 35% of its reference limit, then labelling each row with a
weighted risk score:

```
score = sum(weight_i * measured_i / limit_i) + shift_penalty
score >= 0.58 -> critical
score >= 0.42 -> major
else          -> minor
```

A quarter of the generated rows have one signal deliberately pushed out of spec
while the rest stay nominal. Without those one-sided excursions the model never
sees the case that matters most: a single severe measurement surrounded by good
ones.

`app/model.py` fits the classifier on **ratios against the reference limits**
rather than raw physical units (see `InspectionFeatureBuilder`). Once the
features are ratios, severity is a linear function of them, so the pipeline uses
multinomial **logistic regression** with linear decision boundaries.

A random forest was tried first and rejected: axis-aligned splits approximate a
diagonal boundary poorly, which made the model unstable near the thresholds and
caused it to under-call a lone severe measurement. Logistic regression is both
more accurate here and far cheaper to train.

Reference metrics at `samples=1500, seed=42`: accuracy ~0.99, macro-F1 ~0.99,
class split 45% minor / 37% major / 18% critical, training under 0.05s.

The fitted pipeline is persisted to `artifacts/severity_model.joblib` via joblib.
On startup the service loads the artifact and trains a fresh model if none
exists. `POST /train` retrains on demand.

## Tests

```bash
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

## Branch rules

Commit to the `ai` branch only. Never edit `backend/`, `frontend/` or
`integration/`. See `CONTRIBUTING.md` at the repo root.
