# Tasks

## Epics

- [ ] E1 — Foundation — project scaffold, config, tooling, AI harness (Claude Code skills, MCP access)
- [ ] E2 — Data Layer — SQLite schema + connectivity, ChromaDB, Google Sheets wiring, DB skill for Claude Code
- [ ] E3 — Market Connectivity — Alpaca, Finnhub, TwelveData clients + wrappers
- [ ] E4 — Universe Management — ticker whitelist pipeline, SIC filtering, classification, refresh cadence
- [ ] E5 — Portfolio Management — positions, expiry checks, close logic, trade recording, learnings capture
- [ ] E6 — Candidate Pipeline — screeners, Stage 1 quant filters, Stage 2 scoring/ranking
- [ ] E7 — Research & Intelligence — Stage 3 deep research, LLM summarization, sentiment agents, caching
- [ ] E8 — Trade Execution — position sizing, constraint checks, order placement, regime filter
- [ ] E9 — Learning Loop — trade outcome analysis, meta-learnings, shadow tracking, score multiplier proposals
- [ ] E10 — Observability — logging, Metabase setup, Google Sheets human-readable views

## Tasks

### E2 - Data Layer

- [x] Set up a Google Sheet for the project (test and prod)
- [x] Wire Google Sheets connectivity (service account + gspread, typed `SheetsClient` with full CRUD on `universe` and `holdings`, `--debug` flag selects test vs prod sheet)
- [ ] Define schemas for the remaining tabs (`closed`, `learnings`)
