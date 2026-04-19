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

### E1 - Foundation

- [ ] Scaffold the repo structure (pipelines/, agents/, tools/, config/, tests/)
- [ ] pydantic-settings config class with env vars
- [ ] Write a CLAUDE.md that gives Claude Code the lay of the land — project purpose, repo structure, conventions, what not to touch

### E2 - Data Layer

- [ ] Set up a Google Sheet for the project (test and prod)
- [ ] Set up SQLite (test and prod)
- [ ] Set up ChromaDB (test and prod)
- [ ] Give Claude and Cursor skills to access the Google Sheets, SQLite and ChromaDB and pipeline execution with test environments
