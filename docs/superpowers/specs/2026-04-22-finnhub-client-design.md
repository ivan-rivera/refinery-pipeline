# Finnhub Client Design

**Date:** 2026-04-22
**Status:** Approved

---

## Overview

Introduce a typed Finnhub client into the pipeline's integration layer. Finnhub is the **qualitative and identity data source** — it owns company metadata, news, and fundamentals. TwelveData owns price time series and technical indicators. Reddit owns social sentiment.

---

## API Scope

Four methods are in scope for v1, all available on the free tier:

| Method | SDK call | Used by | Returns |
|---|---|---|---|
| `get_company_profile(symbol)` | `company_profile2(symbol=...)` | Universe Refresh (classification) | `CompanyProfile \| None` |
| `get_company_news(symbol, from_date, to_date)` | `company_news(symbol, _from, to)` | Stage 3 deep research | `list[NewsArticle]` |
| `get_basic_financials(symbol)` | `company_basic_financials(symbol, "all")` | Universe Refresh, Stage 2 scoring | `BasicFinancials \| None` |
| `search_symbols(query)` | `symbol_search(query)` | Universe Refresh (ticker discovery) | `list[SymbolMatch]` |

**Explicitly out of scope:**
- Real-time quotes → Alpaca or TwelveData
- OHLCV / technical indicators → TwelveData
- News sentiment endpoint (premium) → Stage 3 LLM agents handle sentiment
- WebSocket streaming → batch pipeline, not needed
- Earnings calendar, SEC filings → deferred

---

## File Structure

```
src/
  integrations/
    finnhub/
      __init__.py        # exports FinnhubClient, make_finnhub_client
      client.py          # FinnhubClient class + factory
  schemas/
    finnhub.py           # Pydantic response models
  config.py              # gains finnhub_api_key field

tests/
  integrations/
    test_finnhub_client.py

.claude/
  skills/
    finnhub-debug.md     # repo-scoped debugging skill
```

---

## Typed Models (`src/schemas/finnhub.py`)

All fields Finnhub may omit — especially common for junior miners — are typed as `float | None`. String fields default to `""` rather than `None`.

### SDK field mappings

| Model field | SDK source |
|---|---|
| `CompanyProfile.name` | `company_profile2()["name"]` |
| `CompanyProfile.exchange` | `company_profile2()["exchange"]` |
| `CompanyProfile.sector` | `company_profile2()["gicsSector"]` |
| `CompanyProfile.industry` | `company_profile2()["finnhubIndustry"]` |
| `CompanyProfile.country` | `company_profile2()["country"]` |
| `CompanyProfile.market_cap` | `company_profile2()["marketCapitalization"]` (millions USD) |
| `NewsArticle.published_at` | `company_news()[n]["datetime"]` (Unix UTC → timezone-aware `datetime`) |
| `NewsArticle.headline` | `company_news()[n]["headline"]` |
| `NewsArticle.summary` | `company_news()[n]["summary"]` |
| `NewsArticle.source` | `company_news()[n]["source"]` |
| `NewsArticle.url` | `company_news()[n]["url"]` |
| `BasicFinancials.week_52_high` | `metric["52WeekHigh"]` |
| `BasicFinancials.week_52_low` | `metric["52WeekLow"]` |
| `BasicFinancials.beta` | `metric["beta"]` |
| `BasicFinancials.avg_vol_10d` | `metric["10DayAverageTradingVolume"]` (millions shares) |
| `SymbolMatch.symbol` | `symbol_search()["result"][n]["symbol"]` |
| `SymbolMatch.description` | `symbol_search()["result"][n]["description"]` |
| `SymbolMatch.security_type` | `symbol_search()["result"][n]["type"]` |

---

## Client Design (`src/integrations/finnhub/client.py`)

`FinnhubClient` wraps an injected `finnhub.Client` instance, mirroring the `SheetsClient(gc, sheet_id)` pattern. The factory owns construction.

**Error handling:**
- Empty/no-data SDK responses → `None` (single-item) or `[]` (list)
- `finnhub.FinnhubAPIException` → propagates to caller; rate limiting and retry are pipeline-level concerns
- Rate limit: 60 req/min on free tier, documented in module docstring, not enforced by client

**Factory:**
```python
def make_finnhub_client(settings: Settings) -> FinnhubClient:
    if not settings.finnhub_api_key:
        raise ValueError("FINNHUB_API_KEY is not set")
    return FinnhubClient(finnhub.Client(api_key=settings.finnhub_api_key))
```

---

## Settings (`src/config.py`)

One new field:

```python
finnhub_api_key: str = Field(default="", alias="FINNHUB_API_KEY")
```

`FINNHUB_SECRET_KEY` (present in `.env`) is not surfaced — it is reserved for future WebSocket work and unused by the sync REST client.

---

## Testing (`tests/integrations/test_finnhub_client.py`)

Minimal set covering non-trivial logic only. Happy-path field mapping is skipped — Pydantic validates types at runtime.

**Unit tests** (mock `finnhub.Client`, no network):

| Test | What it verifies |
|---|---|
| `test_make_finnhub_client_raises_on_missing_key` | Empty `finnhub_api_key` → `ValueError` |
| `test_get_company_news_converts_unix_timestamp` | Unix int → correct `datetime` |
| `test_get_basic_financials_handles_missing_metrics` | Partial metric dict → `None` fields, no crash |
| `test_get_company_profile_returns_none_on_empty_response` | Empty SDK dict → `None` |

**Integration tests** (marked `@pytest.mark.integration`, skipped without `FINNHUB_API_KEY`, use `GDX` as stable reference ticker):

| Test | What it verifies |
|---|---|
| `test_integration_get_company_profile` | Real profile returned and parses cleanly |
| `test_integration_get_company_news` | Real articles returned for past 7 days |
| `test_integration_get_basic_financials` | Real metrics returned, none raises |
| `test_integration_search_symbols` | Real search result for "gold" contains at least one match |

---

## Debugging Skill (`.claude/skills/finnhub-debug.md`)

A repo-scoped skill file (not global) that instructs Claude how to call Finnhub directly via Bash one-liners using the `finnhub-python` SDK and the `FINNHUB_API_KEY` from the environment. Covers all four in-scope methods with copy-paste examples. No key is hardcoded.
