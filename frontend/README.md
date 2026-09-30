# Frontend

React + Vite dashboard for the Inspection System. Owner: **Frontend developer**.

## Run locally

```bash
npm install
npm run dev
```

Open <http://localhost:5173>. The backend must be running on port 8000 — start
the AI service first, then the backend (see the service READMEs).

## Scripts

| Command           | Purpose                              |
| ----------------- | ------------------------------------ |
| `npm run dev`     | Dev server with hot reload           |
| `npm run build`   | Production build into `dist/`        |
| `npm run preview` | Serve the built bundle locally       |
| `npm test`        | Vitest suite (single run)            |
| `npm run test:watch` | Vitest in watch mode             |
| `npm run lint`    | ESLint                               |

## Configuration

Set `VITE_API_URL` to point at a different backend. Defaults to
`http://localhost:8000`.

```bash
# .env.local
VITE_API_URL=http://localhost:8000
```

## Layout

```
src/
  App.jsx                     page shell, data fetching, actions
  lib/api.js                  fetch wrapper; turns error payloads into messages
  lib/form.js                 form state, validation, payload building
  components/
    HealthBar.jsx             backend / database / AI status
    StatsBar.jsx              dashboard summary cards
    InspectionForm.jsx        create-an-inspection form
    InspectionList.jsx        filterable table with row detail
    SeverityBadge.jsx         colour-coded severity and status pills
  __tests__/                  Vitest + Testing Library specs
```

## Behaviour worth knowing

- Creating a record shows the AI verdict inline. If the AI service is
  unreachable the record is still saved and the UI says so, offering
  **Re-predict** to backfill once the service returns.
- The form validates client-side against the same ranges the backend enforces,
  but the backend remains the authority and its error messages are surfaced.
- Status and severity are never set by the UI; they come from the backend.

## Branch rules

Commit to the `frontend` branch only. Never edit `ai/`, `backend/` or
`integration/`. See `CONTRIBUTING.md` at the repo root.
