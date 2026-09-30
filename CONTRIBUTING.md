# Contributing

Five people, three components, one demo. Read this once, then follow the branch
you own.

## Team

| # | Person    | Role                              | Owns                                                                                       | Branch(es)                                | GitHub handle |
| - | --------- | --------------------------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------- | ------------- |
| 1 | Tharun    | Frontend                          | `frontend/`                                                                                | `frontend`                                | tharun        |
| 2 | Upasana   | Backend API                       | `backend/app/routers/inspections.py`, `backend/app/schemas.py`, `backend/app/ai_client.py`  | `backend-api`                             | upasana       |
| 3 | Preethi   | AI model / prediction             | `ai/`                                                                                      | `ai`                                      | preethi       |
| 4 | Ramya     | Database + history                | `backend/app/models.py`, `backend/app/database.py`, `backend/app/config.py`, `backend/app/routers/history.py` | `backend-data`              | ramya         |
| 5 | Yashwanth | Integration + GitHub + final testing | `integration/`, `.github/`, `backend/app/main.py`, `backend/tests/conftest.py`, `docs/`, `DEMO.md` | `integration`, `testing`, `demo`, `main`  | yashwanth     |

Handles are assumed to match these names. Correct them in this table if not —
reviewers use it to know who to ask.

> Upasana and Ramya both work on the backend, on **separate branches** split by
> layer: Upasana owns the API layer, Ramya the data layer. See below.

## The one rule that prevents most conflicts

**Only edit files listed against your name above.** If a change needs a file
owned by someone else, that is a conversation, not an edit.

Everyone edits a disjoint set of files, so merging the four component branches
into `integration` stays conflict-free. Git merges file by file, not folder by
folder, so `backend-api` and `backend-data` both carrying `backend/` is fine —
they simply never touch the same file inside it.

The two backend branches each keep the **whole** `backend/` directory, not just
their own files. That is deliberate: it lets Upasana boot the backend and run
its test suite on `backend-api`, and Ramya do the same on `backend-data`,
without waiting for the other to merge. The copy of a file you do not own is
there to keep the service runnable, not as an invitation to edit it. Git
resolves the duplicated files silently on merge, because only one branch ever
changes any given file, so merge order between the two does not matter.

### The two shared backend files

`backend/app/main.py` (registers every router) and `backend/tests/conftest.py`
(test fixtures) are both needed by Upasana and Ramya, so they are owned by
Yashwanth. Do not edit either one. If you need a change in one of them, raise an
issue describing it and it lands as a small standalone PR on `integration` —
a few lines, applied by the owner, nothing bundled with it.

## Branches

| Branch        | Who commits here        | Merges into                     |
| ------------- | ----------------------- | ------------------------------- |
| `ai`          | Preethi                | `integration`                   |
| `backend-api` | Upasana                | `integration`                   |
| `backend-data`| Ramya                  | `integration`                   |
| `frontend`    | Tharun                 | `integration`                   |
| `integration` | Yashwanth              | `testing`                       |
| `testing`     | Yashwanth              | `demo`                          |
| `demo`        | Yashwanth              | `main`                          |
| `main`        | nobody commits directly | —                               |

`main` is the demo release. It is protected: no direct pushes, two approvals.

## Daily work

### Pick up a fix from `main`

Do **not** merge `main` into your branch. `main` holds a full release with all
three services in it, so merging would pull the other components onto your
branch and break the separation. Cherry-pick the one commit you need:

```bash
git fetch origin
git log --oneline origin/main ^backend-api    # commits on main you do not have
git cherry-pick <sha>
git push
```

Cross-service changes go to Yashwanth and travel the full pipeline.

Start the day with `git fetch origin` so you can see what has landed.

### Add a change

For anything more than a small fix, use a short-lived feature branch off your
own component branch:

```bash
git switch backend-api          # or backend-data, for Ramya
git pull
git switch -c backend-api/validate-notes-length
# ... work ...
git add backend/app/schemas.py   # stage only the files you own
git commit -m "backend: cap notes length at 2000 characters"
git push -u origin backend-api/validate-notes-length
```

Open a PR into `backend-api` (not `main`), fill in the template, wait for CI.

For small changes, commit straight to your component branch.

### Merge order

Never merge into a branch that is further down the pipeline than your target.
The order is always:

```
ai / backend / frontend  ->  integration  ->  testing  ->  demo  ->  main
```

## Commit messages

Format: `<scope>: <what changed, in the imperative>`

```
ai: normalise measurements by reference limit before classifying
backend: return 409 when part_serial already exists
frontend: show the AI warning banner when a verdict is missing
integration: add e2e coverage for the re-predict path
```

Keep each commit to one logical change. The first line should read as a complete
sentence on its own.

## Before you open a PR

```bash
# AI or backend
cd ai      && pytest -q && ruff check .
cd backend && pytest -q && ruff check .

# frontend
cd frontend && npm run lint && npm test && npm run build
```

Then check:

- [ ] Files changed only in files you own
- [ ] `backend/app/main.py` and `backend/tests/conftest.py` untouched — if either
      was needed, it is a separate request to Yashwanth
- [ ] Tests added or updated
- [ ] No `.env`, `*.db`, `node_modules/`, `.venv/` or `*.joblib` in the diff
- [ ] CI is green
- [ ] Someone else on the team reviewed it

## Cross-service changes

If a field or endpoint changes shape, it usually has to change in more than one
place — the frontend sends it, the backend validates it, the AI service consumes
it. Do not try to land that in one component's PR.

Instead:

1. Raise an issue describing the new contract.
2. Yashwanth coordinates the change across the branches, or splits it into a
   sequence of backward-compatible PRs (add the new field, switch the consumers,
   then remove the old one).
3. Re-run `integration/tests` before merging to `testing`.

The contract between the services is written down in
`integration/README.md`. Keep it accurate.

## Setting up locally

You only need the service you own, but the full stack is easy enough:

```bash
cd integration
docker compose up -d --build --wait
```

Then:

- frontend <http://localhost:5173>
- backend <http://localhost:8000/docs>
- ai <http://localhost:8001/docs>

For individual service work, see the README inside `ai/`, `backend/` or
`frontend/`.

## Adding a dependency

Add it to the owning service's manifest only, with a pinned version:

```bash
# Python
cd ai && .\.venv\Scripts\python.exe -m pip install <package>==<version>
# then edit requirements.txt to match

# JavaScript
cd frontend && npm install <package> --save-exact
```

Never add a dependency to another service's manifest. That is an integration
change.

## CI

Every push and PR runs lint and tests for the affected component. The
end-to-end job boots the full stack with Docker Compose and runs the cross-service
suite; it only runs on `integration`, `testing`, `demo` and on PRs.

If CI fails, fix it on your own branch. Do not merge around it.
