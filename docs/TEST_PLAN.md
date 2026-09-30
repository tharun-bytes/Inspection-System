# Test plan

Owner: **Yashwanth**. Run against the `testing` branch.

## Before you start

```bash
cd integration
docker compose up -d --build --wait
```

Then <http://localhost:5173> should load with no console errors, and both
`/health` endpoints should report up.

## Automated suites

| Suite          | Command                                        | Expect |
| -------------- | ---------------------------------------------- | ------ |
| AI             | `cd ai && pytest -q`                            | 31 pass |
| Backend        | `cd backend && pytest -q`                       | 33 pass |
| Frontend       | `cd frontend && npm test`                       | 33 pass |
| End-to-end     | `cd integration && pytest`                      | 9 pass  |

Total: 106 automated checks. Anything less is a regression — investigate before
merging.

Lint must also be clean: `ruff check .` in `ai/` and `backend/`, `npm run lint`
in `frontend/`.

## Manual checks

Do these by hand even when the suites are green. They cover the paths a unit
test mocks away.

### Health and resilience

- [ ] With the AI service stopped, create an inspection. The record saves, the UI
      warns that the AI service was unavailable, status is `pending`.
- [ ] Restart the AI service, press **Re-predict**. The record is graded and the
      status updates.
- [ ] With the backend stopped, reload the page. A clear "Backend unreachable"
      banner appears rather than a blank screen.

### Grading correctness

Enter these and confirm the verdict. Severities come from the risk score in
`docs/ARCHITECTURE.md`.

| Part serial | dimension_deviation_pct | roughness | torque | vibration | temp | Expected |
| ----------- | ----------------------- | --------- | ------ | --------- | ---- | -------- |
| T-01        | 0.2                     | 0.4       | 10     | 0.4       | 25   | minor / passed |
| T-02        | 5.0                     | 0.4       | 10     | 0.4       | 25   | major / review  |
| T-03        | 12.0                    | 0.4       | 10     | 0.4       | 25   | critical / failed |
| T-04        | 0.2                     | 0.4       | 10     | 0.4       | 25   | minor, but shift=night nudges the score up |
| T-05        | 3.0, all others nominal  | 0.4       | 10     | 0.4       | 25   | minor — a *lone* marginal reading is not escalated |

- [ ] Verdicts match the table.
- [ ] Confidence is between 0 and 1 and shown as a percentage.
- [ ] A lone out-of-spec measurement still escalates (this is the case a tree
      model got wrong; `ai/tests/test_model.py` guards it).

### Data integrity

- [ ] Creating a serial that already exists shows a conflict error, not a crash.
- [ ] Measurements outside the allowed range are rejected with a readable
      message naming the field.
- [ ] Blank serial, part name or inspector are rejected.
- [ ] Deleting a record removes it from the list and the totals update.

### Filtering and stats

- [ ] Filtering by status and by severity narrows the table.
- [ ] The summary cards agree with the rows: critical count matches the filter
      result for `critical`.
- [ ] With no records, the table shows the empty state and the critical rate is
      `0%`, not blank or `NaN`.
- [ ] After deleting every record, stats return to zero.

### UI behaviour

- [ ] Submitting an empty form shows inline field errors and sends no request.
- [ ] Correcting a field clears its error as you type.
- [ ] **Details** expands a row to show all measurements.
- [ ] The layout holds up at 1280px and at a phone width.
- [ ] No errors in the browser console.

## Regression tests to add

Every bug found on `testing` needs a test that fails without the fix. Put
component-level regressions in the owning component's suite, and cross-service
ones in `integration/tests/test_e2e.py`.

## Sign-off

`testing -> demo` only when:

- [ ] all 106 automated checks pass
- [ ] lint clean in all three components
- [ ] every manual check above is ticked
- [ ] no open blocker issues
