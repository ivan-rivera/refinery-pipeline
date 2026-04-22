# TwelveData Integration Design

**Date:** 2026-04-22
**Status:** Approved
**Epic:** E3 — Market Connectivity

---

## Context

The pipeline pulls data from three external sources:

| Source | Role |
|---|---|
| TwelveData | Quantitative backbone — OHLCV price/volume history |
| Finnhub | Qualitative layer — news, sentiment, fundamentals |
| Alpaca | Execution only — trading and portfolio management, no data |
| Reddit | Social sentiment (separate, future) |

This document specifies the TwelveData integration only.

---

## Scope

### TwelveData client owns

- Daily OHLCV bars for any symbol (universe tickers + benchmarks: GDX, GDXJ, COPX, DXY)
- Batch fetching — multiple symbols in one SDK call
- Split-adjusted prices (`adjust="splits"` default)
- Raw data delivery only — no derived computation

### TwelveData client does NOT own

- Derived indicators (ATR, SMA, returns, volume ratios) — computed by pipeline stages from raw OHLCV using pandas
- Caching — the architecture's cache layer owns this (ARCHITECTURE.md §5)
- Intraday or streaming data — daily bars suffice for a 5–28 day swing horizon
- Fundamentals, news, or sentiment — Finnhub client (E3, separate ticket)

---

## Component Layout

```
src/integrations/twelvedata/
    __init__.py          # empty package marker
    client.py            # TwelveDataClient + make_twelvedata_client

src/config.py            # add twelvedata_api_key: str field

pyproject.toml           # add twelvedata + pandas dependencies

tests/integrations/
    __init__.py
    test_twelvedata.py   # unit tests (mocked SDK)

.claude/skills/
    twelvedata-debug.md  # project-level debugging skill
```

Mirrors the `src/integrations/sheets/` structure. `make_twelvedata_client(settings)` is the single entry point for the rest of the codebase.

---

## Client API Surface

```python
class TwelveDataClient:
    def get_ohlcv(
        self,
        symbols: list[str],
        *,
        outputsize: int = 100,
        interval: str = "1day",
    ) -> dict[str, pd.DataFrame]: ...

def make_twelvedata_client(settings: Settings) -> TwelveDataClient: ...
```

### `get_ohlcv` contract

- `outputsize=100` covers ~5 months of daily bars — sufficient for 50d/200d MA and ATR(14)
- Returns `dict[str, pd.DataFrame]`, one entry per symbol that returned data successfully
- Each DataFrame: columns `open`, `high`, `low`, `close`, `volume` (`float64`), indexed by `pd.DatetimeIndex` sorted ascending (oldest row first, most recent row last)
- Single-symbol calls return a one-entry `dict` — callers always get the same shape

### `make_twelvedata_client` contract

- Raises `ValueError` if `settings.twelvedata_api_key` is blank — fail fast before any network call

---

## Error Handling

| Failure | Behaviour |
|---|---|
| Blank/invalid API key | `ValueError` in `make_twelvedata_client` — no network call made |
| Symbol not found / delisted | Log warning, skip symbol, return data for the rest — a bad ticker must not abort a full universe fetch |
| Network / API error (5xx, timeout) | SDK retry logic propagates; if exhausted, exception bubbles to caller — no silent swallowing, no stale data returned |

No custom retry logic — the `twelvedata` SDK handles that. Stale-data prevention is deferred to the cache layer (ARCHITECTURE.md §5).

---

## Testing

Three unit tests, all mocked at the `TDClient` boundary:

| Test | Covers |
|---|---|
| Happy path — multiple symbols | Returns `dict[str, pd.DataFrame]` with correct columns, `DatetimeIndex`, ascending order |
| Partial failure — one symbol errors | Bad symbol absent from result; valid symbols still present |
| Missing API key | `make_twelvedata_client` raises `ValueError` before touching the network |

No integration tests in this PR. Live-API tests belong in a separately-skipped suite once the client is wired into the pipeline.

---

## Debugging Skill

**File:** `.claude/skills/twelvedata-debug.md`
**Scope:** project-local (not global)

Instructs Claude to instantiate `TwelveDataClient` via the project factory (reads API key from `.env` automatically) and run read-only queries via Bash. Covers:

- Fetch N bars of OHLCV for one or more tickers and inspect the DataFrame
- Check the most recent close price
- Verify benchmarks (GDX, GDXJ, COPX, DXY) are returning data
- Spot-check that a bad/delisted ticker is gracefully omitted

The skill is strictly read-only — no mutations.

---

## Settings Change

`src/config.py` gains one new field:

```python
twelvedata_api_key: str = Field(default="", alias="TWELVEDATA_API_KEY")
```

The `.env` already contains `TWELVEDATA_API_KEY`. No secrets change required.

---

## Dependencies Added

| Package | Reason |
|---|---|
| `twelvedata` | Official Python SDK — handles batching, rate limiting, retry |
| `pandas` | Return type for OHLCV data; inevitable dependency for all numerical pipeline work |
