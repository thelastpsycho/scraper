# Hotel Inventory & Revenue Automation

Flask and Vue 3 application for PMS inventory scraping, D-EDGE inventory
exports, yield/allotment calculations, and optional PMS/D-EDGE updates.
The seven-step pipeline supports per-stage selection and an SSE progress log.

## Setup

1. `pip install -r backend/requirements-dev.txt`
2. Copy `backend/.env.example` to `backend/.env`; configure distinct random
   `APP_ACCESS_TOKEN` and `APP_SESSION_SECRET` values (32+ characters), plus
   provider credentials as needed. See `SECURITY.md`.
3. `cd backend && python run.py` (defaults to `127.0.0.1:5666`).
4. `cd frontend && npm ci && npm run dev`; Vite proxies `/api`.
5. Open the app and sign in using `APP_ACCESS_TOKEN`.

Existing SQLite databases, uploads, diagnostic artifacts, and the D-EDGE
persistent browser profile remain under `backend/app/scraper/` and are
ignored by Git.

## Tests

- `PYTHONPATH=backend pytest -q backend/tests`
- `cd frontend && npm run build`

GitHub Actions checks the Python tests and Vue/TypeScript build on PRs and
updates to `main`. Tests do not modify external PMS/D-EDGE accounts.

## Code layout

- `backend/app/integrations/` — PMS/D-EDGE browser automation.
- `backend/app/inventory/` — processing and SQLite persistence.
- `backend/app/revenue/` — yield logic.
- `backend/app/pipeline/` — orchestration.
- `backend/app/routes/` — stable API routes and auth.
- `frontend/src/views/` — Vue router pages.

Review `ALLOCATION_LOGIC.md`, `changes.md`, and `SECURITY.md` before
changing room-allocation rules or production access.
