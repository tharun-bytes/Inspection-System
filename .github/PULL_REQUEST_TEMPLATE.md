## What does this change?

<!-- One or two sentences. Link the issue if there is one. -->

## Component

<!-- Tick one. This must match the branch you opened the PR from. -->

- [ ] `ai/` — severity model and AI service
- [ ] `backend/` — inspection API
- [ ] `frontend/` — React dashboard
- [ ] `integration/` — cross-service wiring, compose, e2e tests
- [ ] root/docs/CI

## Target branch

<!-- PRs from ai/backend/frontend go to their own long-lived branch. -->

- [ ] `ai` / `backend` / `frontend` (routine change to my component)
- [ ] `integration` (component work that is ready to combine with the others)
- [ ] `testing` (a test-only change)
- [ ] `main` (release: testing -> demo -> main)

## How was this verified?

<!-- CI runs pytest / vitest automatically. Say what you ran locally too. -->

- [ ] `pytest` in the affected service
- [ ] `npm test` in `frontend/` (if touched)
- [ ] Ran the stack and clicked through the change

## Checklist

- [ ] I did not edit files outside my component's directory
- [ ] Tests added or updated for the change
- [ ] `ruff check .` / `npm run lint` clean
- [ ] No secrets, `.env` files or trained model artifacts committed
- [ ] Anything a reviewer should know is in the notes below

## Notes for the reviewer

<!-- Gotchas, follow-ups, things you deliberately left out. -->
