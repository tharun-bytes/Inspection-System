# Contributing

Five people, three components, one demo. Read this once, then follow the branch
you own.

## Team

| Role                      | Owns         | Branch(es)                    | GitHub handle |
| ------------------------- | ------------ | ----------------------------- | ------------- |
| AI developer              | `ai/`        | `ai`                          | _TBD_         |
| Backend developer         | `backend/`   | `backend`                     | _TBD_         |
| Frontend developer        | `frontend/`  | `frontend`                    | _TBD_         |
| Integration developer     | `integration/`, CI, releases | `integration`, `demo`, `main` | _TBD_         |
| Test engineer             | test plans, e2e coverage | `testing`             | _TBD_         |

> Fill in the handles before your first PR so reviewers know who to ask.

## The one rule that prevents most conflicts

**Only edit files inside the directory you own.** If a change needs a
cross-service edit, it belongs to the integration developer.

The three component branches touch disjoint paths, so merging them into
`integration` is essentially conflict-free. The moment two people edit the same
file on different branches, that stops being true.

## Branches

| Branch        | Who commits here        | Merges into                     |
| ------------- | ----------------------- | ------------------------------- |
| `ai`          | AI developer            | `integration`                   |
| `backend`     | Backend developer       | `integration`                   |
| `frontend`    | Frontend developer      | `integration`                   |
| `integration` | Integration developer   | `testing`                       |
| `testing`     | Test engineer           | `demo`                          |
| `demo`        | Integration developer   | `main`                          |
| `main`        | nobody commits directly | —                               |

`main` is the demo release. It is protected: no direct pushes, two approvals.

## Daily work

### Pick up a fix from `main`

Do **not** merge `main` into your branch. `main` holds a full release with all
three services in it, so merging would pull the other components onto your
branch and break the separation. Cherry-pick the one commit you need:

```bash
git fetch origin
git log --oneline origin/main ^ai     # commits on main you do not have
git cherry-pick <sha>
git push
```

Cross-service changes go to Yashwanth and travel the full pipeline.

Start the day with `git fetch origin` so you can see what has landed.

### Add a change

For anything more than a small fix, use a short-lived feature branch off your
own component branch:

```bash
git switch backend
git pull
git switch -c backend/validate-notes-length
# ... work ...
git add backend/
git commit -m "backend: cap notes length at 2000 characters"
git push -u origin backend/validate-notes-length
```

Open a PR into `backend` (not `main`), fill in the template, wait for CI.

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

- [ ] Files changed only inside your directory
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
2. The integration developer coordinates the change across the branches, or
   splits it into a sequence of backward-compatible PRs (add the new field,
   switch the consumers, then remove the old one).
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
