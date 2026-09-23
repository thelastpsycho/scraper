# Runtime data directory

This folder is retained for backward compatibility.

Source modules were moved out of `app/scraper/` during the Phase 1 structure refactor, but runtime files intentionally remain here:

- `data/` — SQLite databases, uploads, and debug artifacts
- `.dedge_profile/` — persistent D-EDGE Chrome profile (ignored by git)

Application code should use `app.infrastructure.paths` rather than building these paths manually.
