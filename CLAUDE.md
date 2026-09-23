# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## What this is

A hotel inventory and revenue-automation tool. Selenium collects inventory from the hospitality PMS and D-EDGE, the backend normalizes and combines those datasets, a yield engine calculates online allocation/BAR decisions, and automation flows can push allotment and pricing changes back to the PMS and D-EDGE.

- `backend/` — Flask API, data processing, Selenium integrations, and automation pipeline
- `frontend/` — Vue 3 + TypeScript + Vite SPA

## Commands

Backend (from `backend/`):

```bash
pip install -r requirements.txt
python run.py
```

Frontend (from `frontend/`):

```bash
npm install
npm run dev
npm run build
npm run preview
```

There is currently no automated test suite or lint script configured.

## Backend architecture

`backend/app/__init__.py` is the Flask app factory and registers three blueprints:

- `routes/main.py` — individual scrape/process/yield/allotment/BAR actions and SSE progress streams
- `routes/database_routes.py` — read-only SQLite data endpoints
- `routes/pipeline_routes.py` — end-to-end pipeline control and SSE progress stream

Source code is organized by responsibility:

- `integrations/pms/` — hospitality PMS scraping and allotment automation
- `integrations/dedge/` — D-EDGE inventory scraping and BAR updates
- `inventory/` — PMS/CM processing, inventory combination, allocation persistence
- `revenue/` — yield engine and BAR-rate processing
- `pipeline/` — full workflow orchestration
- `infrastructure/` — shared runtime-path helpers

### Runtime data

For backward compatibility, runtime data intentionally remains in:

`backend/app/scraper/data/`

The source-code refactor does **not** move existing SQLite databases, uploads, screenshots, or HTML debug artifacts. The persistent D-EDGE Chrome profile also remains at:

`backend/app/scraper/.dedge_profile/`

Use `infrastructure/paths.py` instead of constructing these paths manually.

### Data pipeline

1. `integrations/pms/inventory_scraper.py` — scrapes PMS availability and writes `pms_inventory_raw.db`, then runs PMS processing.
2. `inventory/pms_processor.py` — writes `pms_inventory_processed.db`.
3. `integrations/dedge/inventory_scraper.py` — exports D-EDGE room planning data and runs CM processing.
4. `inventory/channel_manager_processor.py` — writes `cm_inventory_processed.db`.
5. `inventory/inventory_combiner.py` — writes `combined_inventory.db`.
6. `revenue/yield_engine.py` — writes `inventory_allocation.db` (table `daily_inventory_allocation`).
7. `integrations/pms/allotment_updater.py` and `other_room_allotment_updater.py` — push calculated allotments into the PMS.
8. `integrations/dedge/bar_updater.py` — pushes BAR levels into D-EDGE.

`pipeline/runner.py` orchestrates the automated seven-step workflow:

PMS scrape → D-EDGE scrape → combine → yield → verify → PMS allotment → D-EDGE BAR.

### Progress streaming

Long-running operations run in background threads and use SSE for live logs.

- PMS scraping uses `scraping_progress` in `routes/main.py`.
- Allotment and BAR operations share `log_queue` from `app/shared.py`.
- The full pipeline republishes progress through its own `pipeline_queue`.

## Frontend architecture

Vue Router lives in `src/router.ts`. Routed components use the `*View.vue` naming convention:

- `DashboardView.vue`
- `InventoryCollectionView.vue`
- `InventoryDataView.vue`
- `YieldManagementView.vue`
- `AllotmentManagementView.vue`
- `BarPricingView.vue`
- `AutomationPipelineView.vue`

The existing public route URLs remain unchanged.

The shared axios instance uses a relative base URL and Vite proxies `/api` to the Flask backend during development.

## Known security concern

The DeepSeek-backed chat/assistant page (`InventoryAssistantView.vue`) was removed because it called DeepSeek directly from the browser with a hardcoded API key. That key is still in repository history and must be rotated/revoked - removing the source file does not do that.
