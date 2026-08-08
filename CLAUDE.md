# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A hotel revenue-management tool: a Selenium scraper pulls room-inventory data out of a hospitality PMS (`fo.hospitality.mykg.id`), combines it with manually-uploaded Channel Manager data, and runs a yield/demand pricing matrix over the result. A Vue frontend drives each stage and visualizes the output.

- `backend/` — Flask API + Selenium scraping/automation pipeline
- `frontend/` — Vue 3 + TypeScript + Vite SPA

## Commands

Backend (from `backend/`):
```
pip install -r requirements.txt
python run.py          # runs on http://0.0.0.0:5666 with debug=True
```

Frontend (from `frontend/`):
```
npm install
npm run dev             # Vite dev server on :5173, proxies /api -> 127.0.0.1:5666
npm run build            # vue-tsc typecheck + vite build
npm run preview
```

There is no test suite or lint script configured in either package — don't assume `npm test`/`npm run lint` exist.

## Backend architecture

`backend/app/__init__.py` is a Flask app factory that registers two blueprints:
- `routes/main.py` — triggers each pipeline stage and streams progress
- `routes/database_routes.py` — read-only GET endpoints that dump each SQLite DB in `scraper/data/` as JSON

CORS is hardcoded in `create_app()` to a fixed list of frontend origins (`localhost:5173`, `127.0.0.1:5173`, a LAN IP) — update this list if the frontend is served from elsewhere.

### Data pipeline

Each stage in `backend/app/scraper/` reads the previous stage's SQLite DB and writes its own DB + CSV mirror into `backend/app/scraper/data/`. Endpoints check that the required upstream `.db` file exists before running, so stages must execute in order:

1. **`scraper.py`** (`POST /api/scrape`) — Selenium logs into the PMS and scrapes room availability into `pms_inventory_raw.db`.
2. **`process_pms_inventory.py`** — cleans the raw PMS data into `pms_inventory_processed.db`.
3. **`process_cm_inventory.py`** (`POST /api/process-cm`) — processes a Channel Manager Excel file uploaded via `POST /api/upload-cm-excel` (saved as `data/cm_upload.xlsx`) into `cm_inventory_processed.db`.
4. **`combine_inventory.py`** (`POST /api/combine-inventory`) — merges the two processed DBs into `combined_inventory.db`.
5. **`yielder.py`** (`POST /api/yield`, or `POST /api/custom-yield` for a caller-supplied demand/threshold/room-cap config) — applies the yield/demand matrix to produce `inventory_allocation.db` (table `daily_inventory_allocation`).
6. **`update_pms_cm_allotment.py`** / **`update_allotment_dom.py`** (`POST /api/update-allotment`, `POST /api/update-allotment-dom`) — separate Selenium flows that push allotment changes *back* into the PMS. PMS credentials are passed per-request in the JSON body, not stored in env/config.

The `scraper/data/` SQLite files and CSVs are working data (checked in), not fixtures — pipeline stages overwrite them (`if_exists='replace'`).

### Progress streaming

Long-running scrape/update jobs run in background daemon threads and push status onto a shared queue, consumed by an SSE endpoint:
- `scraping_progress` (a `queue.Queue` local to `routes/main.py`) feeds `GET /api/scrape/stream`.
- `log_queue` (`app/shared.py`, a plain module-level `queue.Queue`) feeds `GET /api/update-allotment/stream` and is shared by both allotment-update flows; a `None` sentinel signals stream end.

## Frontend architecture

Vue Router (`src/router.ts`) maps routes almost 1:1 to pipeline stages: `Scraping`, `Yielder`, `Data`, `Allotment`, plus `Chat`. Pinia (`src/stores/index.ts`) holds a generic `mainStore` (loading/error) and a `chatStore` that persists chat history to `sessionStorage`.

The shared axios instance (`src/plugins/axios.ts`) has `baseURL: http://127.0.0.1:5666` hardcoded — in dev this is redundant with the Vite proxy but matters for prod builds.

`Chat.vue` calls the DeepSeek chat completions API directly from the browser (not proxied through the Flask backend) and feeds it the current combined-inventory data as context.

⚠️ `frontend/src/views/Chat.vue` has a live DeepSeek API key hardcoded in the `Authorization` header, shipped to any browser that loads the page and committed to git history. This should be rotated and moved server-side.
