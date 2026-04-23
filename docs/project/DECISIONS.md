# Decisions

This section outlines a log of architectural decisions for record keeping.

## Decision Log

### ADR-001: Structure the trading chain as a pipeline

**Date:** 2026-04-16
**Status:** Accepted

#### Context
The original idea was th set up a server that would periodically launch a background job. This server would also offer extra endpoints. After revising the frequency at which this pipeline would be expected to run, a server felt unnecessary.

#### Decision
Run the pipeline locally on a schedule. If a need eventually emerges to run it remotely, we would go with [Modal](https://modal.com/) to do that.

#### Consequences
- The scheduler is Mac-native in the first iteration
- The job may not run due to the machine being offline

#### Alternatives Considered
FastAPI server

### ADR-002: Use Google Sheets as the database

**Date:** 2026-04-16
**Status:** Accepted

#### Context
We need to store trade metadata, such as the trading thesis, expiry dates, and so on, to do that, we need a storage layer

#### Decision
Google sheets allows us to read and write structured data without the overhead of a fully blown DB. Moving forward, we may choose to introduce ChromaDB for vector storage and SQLite for more complex DB modelling, but for now Google Sheets will be our data storage layer, to keep things simple.

#### Consequences
- We can view and interact with the database
- There is a risk that human modifications may corrupt trade

#### Alternatives Considered
PostgreSQL vs Supabase was considered here, but it was more complex

### ADR-003: Use a Google service account + gspread for Sheets access

**Date:** 2026-04-19
**Status:** Accepted

#### Context
ADR-002 commits the project to Google Sheets as the storage layer. The pipeline runs as an unattended scheduled job, which rules out an interactive OAuth consent flow. We also want the codebase to depend on as small a surface area as possible — direct REST calls against the Sheets API would require us to hand-roll auth, retries, and cell parsing.

#### Decision
- Authenticate with a **Google Cloud service account** whose JSON key path is read from `GOOGLE_CREDS_PATH`. The two project spreadsheets (`GOOGLE_SHEET_ID_TEST`, `GOOGLE_SHEET_ID_PROD`) are explicitly shared with the service account's `client_email`.
- Use **`gspread>=6`** as the client library. It provides native service-account support (`gspread.service_account(filename=...)`), a worksheet-level abstraction (`get_all_values`, `append_row`, `update`, `delete_rows`), and is the de facto Python wrapper for Sheets.
- Test vs prod selection is driven by an explicit CLI `--dry-run` flag, passed to a `make_sheets_client(settings, debug=...)` factory — no env coupling inside components, per the project rule in `CLAUDE.md`.

#### Consequences
- New spreadsheets must be shared with the service account before they become readable/writable; this is an out-of-band operator step.
- The credential file at `GOOGLE_CREDS_PATH` must be a service-account JSON. The OAuth desktop `client_secret_*.apps.googleusercontent.com.json` previously sitting at that path cannot be used as-is and must be replaced.
- We get a small, typed CRUD surface (`SheetsClient.get_universe / append_holding / ...`) with row Pydantic models as the single source of truth for column order; tests can mock `gspread` cleanly without hitting the network.

#### Alternatives Considered
- **OAuth Desktop client** with a stored refresh token: requires a one-time interactive consent and persistent token cache, awkward for headless/scheduled runs.
- **`google-api-python-client` directly**: more boilerplate for what is essentially row-level CRUD; we would re-implement the wrapper that `gspread` already provides.

### ADR-004: Alpaca client scope, wrapper style, and paper/live switching

**Date:** 2026-04-22
**Status:** Accepted

#### Context
Alpaca is the execution platform. The architecture also lists it as a potential market data source alongside Finnhub and TwelveData. A decision was needed on (a) what responsibilities belong to the Alpaca client, (b) how much abstraction to place over the SDK, and (c) how to switch between paper and live accounts.

#### Decision
- **Scope:** `AlpacaClient` handles execution and portfolio management only (`get_account`, `get_all_positions`, `get_open_position`, `close_position`, `submit_order`). All price and volume data comes from Finnhub and TwelveData — Alpaca is not used as a data source.
- **Wrapper style:** Thin delegation wrapper — alpaca-py's `TradingClient` is wrapped with no translation layer. SDK types (`TradeAccount`, `Position`, `Order`, etc.) are intentionally allowed to leak into the trade execution component. That component is small and Alpaca-specific; adding a domain translation layer would be overhead without benefit at this scale.
- **Paper vs live:** Determined entirely by which API keys are configured in the environment. The codebase has no `paper=True/False` flag. `ALPACA_BASE_URL` selects the API endpoint; swapping PROD keys and updating the URL is sufficient to go live — zero code changes required.

#### Consequences
- Finnhub/TwelveData remain the sole sources of OHLCV, volume, and technical indicator data; Alpaca data capabilities are unused for now.
- The trade execution component is the only part of the codebase that imports from `alpaca.*`; the research and scoring pipeline is fully isolated from the SDK.
- Going live requires only an environment change, not a code change.

#### Alternatives Considered
- **Domain-typed facade:** Translate all alpaca-py return types into project-owned Pydantic models. Rejected as over-engineering — the execution component is small and the SDK types are stable.
- **Alpaca as a market data source:** Alpaca provides historical bars and snapshots. Rejected for the initial integration to keep the client scope tight; can be added later if Finnhub/TwelveData prove insufficient.
