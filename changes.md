# changes.md

## Phase 1 — Project structure cleanup

Branch: `refactor/phase-1-project-structure`

This refactor reorganizes source files and naming only. It is intentionally designed to preserve existing application behavior.

### Compatibility guarantees

The following are intentionally unchanged:

- Public Flask API URLs and request/response shapes.
- SQLite database filenames and table names.
- Runtime data location: `backend/app/scraper/data/`.
- D-EDGE persistent Chrome profile location: `backend/app/scraper/.dedge_profile/`.
- PMS and D-EDGE Selenium workflows/selectors.
- Yield/allocation formulas and room caps.
- Pipeline stage order and step IDs.
- Vue route URLs such as `/scraping`, `/yielder`, `/data`, `/allotment`, `/bar-calculator`, `/pipeline`, and `/chat`.

### Backend source moves

| Previous | New |
| --- | --- |
| `backend/app/scraper/scraper.py` | `backend/app/integrations/pms/inventory_scraper.py` |
| `backend/app/scraper/cm_scraper.py` | `backend/app/integrations/dedge/inventory_scraper.py` |
| `backend/app/scraper/update_pms_cm_allotment.py` | `backend/app/integrations/pms/allotment_updater.py` |
| `backend/app/scraper/update_rest_allotment.py` | `backend/app/integrations/pms/other_room_allotment_updater.py` |
| `backend/app/scraper/update_bar.py` | `backend/app/integrations/dedge/bar_updater.py` |
| `backend/app/scraper/process_pms_inventory.py` | `backend/app/inventory/pms_processor.py` |
| `backend/app/scraper/process_cm_inventory.py` | `backend/app/inventory/channel_manager_processor.py` |
| `backend/app/scraper/combine_inventory.py` | `backend/app/inventory/inventory_combiner.py` |
| `backend/app/scraper/allocation_store.py` | `backend/app/inventory/allocation_repository.py` |
| `backend/app/scraper/yielder.py` | `backend/app/revenue/yield_engine.py` |
| `backend/app/scraper/process_bar_rates.py` | `backend/app/revenue/bar_rate_processor.py` |
| `backend/app/pipeline_runner.py` | `backend/app/pipeline/runner.py` |

### New backend packages

- `integrations/pms/` — PMS scraping and allotment automation.
- `integrations/dedge/` — D-EDGE inventory scraping and BAR automation.
- `inventory/` — inventory processing, combination, and allocation persistence.
- `revenue/` — yield and BAR-rate calculations.
- `pipeline/` — end-to-end orchestration.
- `infrastructure/` — shared runtime path helpers.

### Runtime-path compatibility

`backend/app/infrastructure/paths.py` centralizes runtime paths while deliberately pointing to the existing `backend/app/scraper/` runtime folder. This prevents existing local databases, CM uploads, debug artifacts, and the trusted D-EDGE Chrome profile from being lost after the source-code move.

### Frontend view renames

| Previous | New |
| --- | --- |
| `Home.vue` | `DashboardView.vue` |
| `Scraping.vue` | `InventoryCollectionView.vue` |
| `Yielder.vue` | `YieldManagementView.vue` |
| `Data.vue` | `InventoryDataView.vue` |
| `Allotment.vue` | `AllotmentManagementView.vue` |
| `BarCalculator.vue` | `BarPricingView.vue` |
| `Pipeline.vue` | `AutomationPipelineView.vue` |
| `Chat.vue` | `InventoryAssistantView.vue` |

Only component filenames/imports changed; route paths and behavior remain unchanged.

### Documentation

- Updated `CLAUDE.md` to reflect the current project structure and automated CM/pipeline flow.
- Updated `ALLOCATION_LOGIC.md` references to the new yield-engine path.
- Added this change log for future maintainers.

### Not included in this phase

This PR does not intentionally change business logic, security/authentication, queue/job isolation, Selenium behavior, database schemas, or API design. Those should be handled in separate focused PRs.

## Phase 2 — Security, BAR reliability, and regression tests (2026-09-23)

The earlier follow-up commit `6039c53` resolved two stale `current_dir`
debug references and introduced 10-row D-EDGE BAR batches; these fixes are
retained.

### Authentication and credential protection

- API operations now require an operator login session; mutating endpoints
  also require a CSRF token.
- Credentials and the Flask session secret are configured on the backend.
  Flask defaults to loopback with its debugger disabled.
- DeepSeek API calls now use a Flask proxy, and assistant Markdown is sanitized.
- Removed the current source copies of exposed DeepSeek/D-EDGE secrets, plus
  browser-bundled `VITE_*` provider credential defaults.
- **Operator action required:** rotate both previously exposed credentials.
  Git history remains unchanged. See `SECURITY.md`.

### BAR correctness and recovery

- Split contiguous price-level runs at calendar-year boundaries.
- Re-find the Add button while polling and tolerate stale Selenium elements.
- Atomically checkpoint each successfully confirmed BAR batch. Identical-plan
  retries skip already confirmed chunks; changed plans require an operator
  checkpoint reset.
- Pipeline UI and direct BAR endpoint expose explicit checkpoint reset.
- If D-EDGE applied a change but its success response was lost, the operator
  must reconcile the extranet manually before retrying.

### Tests and operations

- Added backend tests for BAR chunking, year-boundary grouping, checkpoint
  recovery, authentication/CSRF, the assistant proxy, and moved-module imports.
- Added GitHub Actions backend test and frontend build checks.
- Declared the missing `tabulate` dependency.
- Restored detailed per-room allocation documentation.
- Added `README.md`, `SECURITY.md`, backend environment examples.

Existing unauthenticated LAN workflows now require login. Local Flask binds
to loopback by default; consult `SECURITY.md` before remote deployment.
