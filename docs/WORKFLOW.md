# Development workflow

Five people, three components, one integration point. This is the branch layout
and the order things are allowed to merge.

## The shape

```
                          main  (demo release - protected)
                            |
          +-----------------+------------------+
          |                 |                  |
      testing            demo                 |
          |                 |                  |
      integration <---------+                  |
          |                                    |
    +-----+-----+---------+                    |
    |     |     |         |                    |
    ai  backend frontend   |                    |
    |     |     |         |                    |
    +-----+-----+---------+                    |
          |                                    |
          +-------------------------------------+
```

| Branch       | Owner                    | Contains                              |
| ------------ | ------------------------ | ------------------------------------- |
| `ai`         | AI developer             | `ai/`                                 |
| `backend`    | Backend developer        | `backend/`                            |
| `frontend`   | Frontend developer       | `frontend/`                           |
| `integration`| Integration developer    | `integration/` + everything merged in  |
| `testing`    | Test engineer            | End-to-end tests, test plan            |
| `demo`       | Integration developer    | Release candidate, demo rehearsal     |
| `main`       | Integration developer    | What the demo actually runs           |

Each developer owns exactly one directory, so the three component branches touch
disjoint paths and merging them into `integration` is essentially conflict-free.

## The flow, in order

1. **Component work** — the AI, backend and frontend developers work in
   parallel on their own branch. Short-lived feature branches off their component
   branch, or commits straight to it for small changes. Never edit another
   component's directory.

2. **Merge into `integration`** — once a component is demonstrable, its branch is
   merged into `integration`. This is the first time the three parts meet. Run
   `docker compose up` and the e2e suite locally before merging.

3. **Merge `integration` into `testing`** — the test engineer runs the full
   suite, works through `docs/TEST_PLAN.md`, and adds regression tests for
   anything that breaks. Fixes go back to the owning component's branch and
   travel the same path again.

4. **Merge `testing` into `demo`** — the release candidate. Rehearse the demo
   end to end on this branch. Only bug fixes at this point, and each one has to
   go back through `integration` and `testing`.

5. **Merge `demo` into `main`** — the version presented. Tag it:

   ```bash
   git tag -a v1.0.0 -m "Demo release v1.0.0"
   git push origin v1.0.0
   ```

## Why the branches are set up this way

Merging three active branches into `main` directly means conflicts land on
whoever happens to be integrating that day, and a broken `main` is a broken demo.
With the staged branches above, `main` only ever receives something that has
already survived integration and testing.

The cost is that merges must travel a few hops. Keep changes small and merge
often — a component branch that drifts for a week makes the `integration` merge
painful for everyone.

## Ground rules

- **One directory per developer.** If a change needs a cross-service edit, it
  belongs to the integration developer.
- **Never commit** `.env` files, `*.db`, `node_modules/`, `.venv/` or trained
  model artifacts. `.gitignore` already covers these — check before committing.
- **CI must be green** before merge. Every PR runs lint and tests for the
  component it touches.
- **Never merge `main` into a component branch.** Cherry-pick the specific fix
  you need instead — see below for why.
- **Small commits with clear messages.** `backend: validate torque range on
  create`, not `fixes`.
- **Two approvals to merge into `main`**, one elsewhere.

## Keeping a component branch current

**Do not merge `main` into a component branch.** `main` is a full release — it
contains all three services. Merging it into `ai` would drag `backend/` and
`frontend/` onto the `ai` branch, and the disjoint-directory setup that keeps
the `integration` merge conflict-free would be gone. This is the single easiest
way to wreck the branch structure.

Component branches only ever move *forward*, through `integration`:

```
ai  ─┐
backend  ─┼─>  integration  ->  testing  ->  demo  ->  main
frontend  ─┘
```

When a fix lands on `main` and you need it on your branch, take just that commit:

```bash
git switch ai
git fetch origin
git log --oneline origin/main ^ai          # find the fix
git cherry-pick <sha>
git push
```

If the fix is cross-service, it goes through Yashwanth and travels the normal
path. That is the whole reason the pipeline exists.

To see how far a component branch has drifted from the release:

```bash
git log --oneline origin/main ^ai
```

## Recovering from a bad `main`

`main` is only ever advanced from `demo`, so a bad release is reverted, not
rewritten:

```bash
git revert -m 1 <merge-sha>
git push origin main
```

Do not force-push to `main`.
