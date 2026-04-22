# Finnhub Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a typed Finnhub integration client providing company profiles, news, basic financials, and symbol search — the qualitative/identity data layer feeding universe refresh and Stage 3 deep research.

**Architecture:** `FinnhubClient` wraps the `finnhub-python` SDK and maps raw dicts to Pydantic models in `src/schemas/finnhub.py`. A `make_finnhub_client(settings)` factory owns construction. Follows the same pattern as `SheetsClient` in `src/integrations/sheets/client.py`.

**Tech Stack:** `finnhub-python` SDK, Pydantic v2, pytest + pytest-mock

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `pyproject.toml` | Modify | Add `finnhub-python` dependency |
| `src/config.py` | Modify | Add `finnhub_api_key` settings field |
| `src/schemas/finnhub.py` | Create | Four Pydantic response models |
| `src/integrations/finnhub/__init__.py` | Create | Re-export `FinnhubClient`, `make_finnhub_client` |
| `src/integrations/finnhub/client.py` | Create | `FinnhubClient` class + factory |
| `tests/integrations/finnhub/__init__.py` | Create | Empty package marker |
| `tests/integrations/finnhub/client_test.py` | Create | Unit + integration tests |
| `.claude/skills/finnhub-debug.md` | Create | Repo-scoped Finnhub debugging skill |

---

### Task 1: Bootstrap — dependency, settings field, empty module files

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/config.py`
- Create: `src/integrations/finnhub/__init__.py`
- Create: `src/integrations/finnhub/client.py`
- Create: `src/schemas/finnhub.py`
- Create: `tests/integrations/finnhub/__init__.py`

- [ ] **Step 1: Add the `finnhub-python` dependency**

Run from the project root (the worktree directory):
```bash
uv add "finnhub-python>=2.4.0"
```
Expected: `pyproject.toml` and `uv.lock` updated, package downloaded.

- [ ] **Step 2: Add `finnhub_api_key` to `Settings`**

In `src/config.py`, add one field to the `Settings` class, after the `google_sheet_id_prod` line:
```python
    finnhub_api_key: str = Field(default="", alias="FINNHUB_API_KEY")
```

The complete `Settings` class should now read:
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    app_name: str = "refinery-pipeline"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    google_creds_path: Path | None = Field(default=None, alias="GOOGLE_CREDS_PATH")
    google_sheet_id_test: str = Field(default="", alias="GOOGLE_SHEET_ID_TEST")
    google_sheet_id_prod: str = Field(default="", alias="GOOGLE_SHEET_ID_PROD")
    finnhub_api_key: str = Field(default="", alias="FINNHUB_API_KEY")

    def sheet_id(self, *, debug: bool) -> str:
        """Return the Google Sheet id for the current environment."""
        return self.google_sheet_id_test if debug else self.google_sheet_id_prod
```

- [ ] **Step 3: Create empty placeholder files**

Create `src/integrations/finnhub/__init__.py` with just a docstring:
```python
"""Finnhub integration."""
```

Create `src/integrations/finnhub/client.py` with just a docstring:
```python
"""Finnhub client — implementation coming in Task 3."""
```

Create `src/schemas/finnhub.py` with just a docstring:
```python
"""Finnhub response models — implementation coming in Task 2."""
```

Create `tests/integrations/finnhub/__init__.py` as an empty file.

- [ ] **Step 4: Verify the project still imports cleanly**

```bash
uv run python -c "from src.config import get_settings; print(get_settings().finnhub_api_key[:4] + '...' if get_settings().finnhub_api_key else 'key empty')"
```
Expected: prints either the first 4 chars of the key (if `.env` is loaded) or `key empty`. Either is fine — the point is no `ImportError`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock src/config.py src/integrations/finnhub/ src/schemas/finnhub.py tests/integrations/finnhub/
git commit -m "chore(deps): add finnhub-python and wire settings field"
```

---

### Task 2: Pydantic response schemas

**Files:**
- Modify: `src/schemas/finnhub.py`

- [ ] **Step 1: Write the four response models**

Replace the contents of `src/schemas/finnhub.py`:
```python
"""Typed response models for Finnhub API data."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CompanyProfile(BaseModel):
    symbol: str
    name: str = ""
    exchange: str = ""
    sector: str = ""
    industry: str = ""
    country: str = ""
    market_cap: float | None = None


class NewsArticle(BaseModel):
    published_at: datetime
    headline: str = ""
    summary: str = ""
    source: str = ""
    url: str = ""


class BasicFinancials(BaseModel):
    symbol: str
    week_52_high: float | None = None
    week_52_low: float | None = None
    beta: float | None = None
    avg_vol_10d: float | None = None


class SymbolMatch(BaseModel):
    symbol: str
    description: str = ""
    security_type: str = ""
```

- [ ] **Step 2: Verify schemas import cleanly**

```bash
uv run python -c "from src.schemas.finnhub import CompanyProfile, NewsArticle, BasicFinancials, SymbolMatch; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add src/schemas/finnhub.py
git commit -m "feat(schemas): add Finnhub typed response models"
```

---

### Task 3: FinnhubClient — TDD

**Files:**
- Create: `tests/integrations/finnhub/client_test.py`
- Modify: `src/integrations/finnhub/client.py`
- Modify: `src/integrations/finnhub/__init__.py`

- [ ] **Step 1: Write all four unit tests**

Create `tests/integrations/finnhub/client_test.py`:
```python
"""FinnhubClient unit tests."""

from __future__ import annotations

import os
from datetime import date, datetime, timezone

import pytest

from src.integrations.finnhub import FinnhubClient, make_finnhub_client


def test_make_finnhub_client_raises_on_missing_key(mocker):
    settings = mocker.MagicMock(finnhub_api_key="")
    with pytest.raises(ValueError, match="FINNHUB_API_KEY"):
        make_finnhub_client(settings)


def test_get_company_profile_returns_none_on_empty_response(mocker):
    sdk = mocker.MagicMock()
    sdk.company_profile2.return_value = {}
    assert FinnhubClient(sdk).get_company_profile("FAKE") is None


def test_get_company_news_converts_unix_timestamp(mocker):
    sdk = mocker.MagicMock()
    sdk.company_news.return_value = [
        {
            "datetime": 1700000000,
            "headline": "Gold surges",
            "summary": "Gold hit a new high.",
            "source": "Reuters",
            "url": "https://example.com",
        }
    ]
    articles = FinnhubClient(sdk).get_company_news("GDX", date(2023, 11, 1), date(2023, 11, 30))
    assert len(articles) == 1
    assert articles[0].published_at == datetime.fromtimestamp(1700000000, tz=timezone.utc)


def test_get_basic_financials_handles_missing_metrics(mocker):
    sdk = mocker.MagicMock()
    sdk.company_basic_financials.return_value = {"metric": {"52WeekHigh": 35.0}}
    result = FinnhubClient(sdk).get_basic_financials("GDX")
    assert result is not None
    assert result.week_52_high == 35.0
    assert result.beta is None
    assert result.avg_vol_10d is None
```

- [ ] **Step 2: Run — verify all four tests fail with ImportError**

```bash
uv run pytest tests/integrations/finnhub/client_test.py -v
```
Expected: 4 tests ERROR — `ImportError: cannot import name 'FinnhubClient'`

- [ ] **Step 3: Implement the complete client**

Replace `src/integrations/finnhub/client.py`:
```python
"""Typed Finnhub client.

Wraps the finnhub-python SDK so the rest of the codebase never sees raw dicts.
Rate limit: 60 requests/min on the free tier — callers are responsible for pacing.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

import finnhub

from src.schemas.finnhub import BasicFinancials, CompanyProfile, NewsArticle, SymbolMatch

if TYPE_CHECKING:
    from src.config import Settings


class FinnhubClient:
    """Typed access to the Finnhub REST API."""

    def __init__(self, client: finnhub.Client) -> None:
        self._client = client

    def get_company_profile(self, symbol: str) -> CompanyProfile | None:
        """Return company profile for `symbol`, or None if Finnhub has no data."""
        data = self._client.company_profile2(symbol=symbol)
        if not data or not data.get("ticker"):
            return None
        return CompanyProfile(
            symbol=data.get("ticker", symbol),
            name=data.get("name", ""),
            exchange=data.get("exchange", ""),
            sector=data.get("gicsSector", ""),
            industry=data.get("finnhubIndustry", ""),
            country=data.get("country", ""),
            market_cap=data.get("marketCapitalization") or None,
        )

    def get_company_news(self, symbol: str, from_date: date, to_date: date) -> list[NewsArticle]:
        """Return news articles for `symbol` between `from_date` and `to_date`."""
        articles = self._client.company_news(
            symbol,
            _from=from_date.strftime("%Y-%m-%d"),
            to=to_date.strftime("%Y-%m-%d"),
        )
        if not articles:
            return []
        return [
            NewsArticle(
                published_at=datetime.fromtimestamp(a["datetime"], tz=timezone.utc),
                headline=a.get("headline", ""),
                summary=a.get("summary", ""),
                source=a.get("source", ""),
                url=a.get("url", ""),
            )
            for a in articles
        ]

    def get_basic_financials(self, symbol: str) -> BasicFinancials | None:
        """Return key financial metrics for `symbol`, or None if unavailable."""
        data = self._client.company_basic_financials(symbol, "all")
        if not data or not data.get("metric"):
            return None
        metric = data["metric"]
        return BasicFinancials(
            symbol=symbol,
            week_52_high=metric.get("52WeekHigh") or None,
            week_52_low=metric.get("52WeekLow") or None,
            beta=metric.get("beta") or None,
            avg_vol_10d=metric.get("10DayAverageTradingVolume") or None,
        )

    def search_symbols(self, query: str) -> list[SymbolMatch]:
        """Search for symbols matching `query`."""
        data = self._client.symbol_search(query)
        if not data or not data.get("result"):
            return []
        return [
            SymbolMatch(
                symbol=r.get("symbol", ""),
                description=r.get("description", ""),
                security_type=r.get("type", ""),
            )
            for r in data["result"]
        ]


def make_finnhub_client(settings: Settings) -> FinnhubClient:
    """Build a FinnhubClient from application settings."""
    if not settings.finnhub_api_key:
        raise ValueError("FINNHUB_API_KEY is not set")
    return FinnhubClient(finnhub.Client(api_key=settings.finnhub_api_key))
```

Replace `src/integrations/finnhub/__init__.py`:
```python
"""Finnhub integration."""

from src.integrations.finnhub.client import FinnhubClient, make_finnhub_client

__all__ = ["FinnhubClient", "make_finnhub_client"]
```

- [ ] **Step 4: Run unit tests — verify all four pass**

```bash
uv run pytest tests/integrations/finnhub/client_test.py -v
```
Expected: 4 tests PASSED.

- [ ] **Step 5: Run the full test suite to check for regressions**

```bash
uv run pytest -v
```
Expected: all existing tests pass alongside the 4 new ones.

- [ ] **Step 6: Commit**

```bash
git add src/integrations/finnhub/ src/schemas/finnhub.py tests/integrations/finnhub/client_test.py
git commit -m "feat(integrations): add FinnhubClient with typed response models"
```

---

### Task 4: Integration tests

**Files:**
- Modify: `tests/integrations/finnhub/client_test.py`

- [ ] **Step 1: Append the four integration tests**

Append to the end of `tests/integrations/finnhub/client_test.py`:
```python


# ---------------------------------------------------------------------------
# Integration tests — skipped unless FINNHUB_API_KEY is set in the environment
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="FINNHUB_API_KEY not set")
def test_integration_get_company_profile():
    from src.config import get_settings
    result = make_finnhub_client(get_settings()).get_company_profile("GDX")
    assert result is not None
    assert result.symbol != ""


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="FINNHUB_API_KEY not set")
def test_integration_get_company_news():
    from datetime import timedelta
    from src.config import get_settings
    today = date.today()
    result = make_finnhub_client(get_settings()).get_company_news(
        "GDX", today - timedelta(days=7), today
    )
    assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="FINNHUB_API_KEY not set")
def test_integration_get_basic_financials():
    from src.config import get_settings
    result = make_finnhub_client(get_settings()).get_basic_financials("GDX")
    assert result is not None


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("FINNHUB_API_KEY"), reason="FINNHUB_API_KEY not set")
def test_integration_search_symbols():
    from src.config import get_settings
    results = make_finnhub_client(get_settings()).search_symbols("gold")
    assert len(results) > 0
```

- [ ] **Step 2: Run integration tests against the live API**

Source the `.env` file (it lives one level above the worktree) and run:
```bash
set -a && source /Users/ivr/Documents/projects/refinery-pipeline/.env && set +a
uv run pytest tests/integrations/finnhub/ -m integration -v
```
Expected: 4 tests PASSED. If `test_integration_get_company_news` returns an empty list, that is acceptable — GDX may have no news in the last 7 days; the test only checks the return type.

- [ ] **Step 3: Commit**

```bash
git add tests/integrations/finnhub/client_test.py
git commit -m "test(integrations): add Finnhub integration tests"
```

---

### Task 5: Debugging skill

**Files:**
- Create: `.claude/skills/finnhub-debug.md`

- [ ] **Step 1: Create the skill file**

Create `.claude/skills/finnhub-debug.md`:
````markdown
---
name: finnhub-debug
description: Read-only debugging access to the Finnhub API. Use to inspect company profiles, news, financials, and symbol search results without running the full pipeline.
---

# Finnhub Debug Access

Use this skill to call Finnhub directly via Bash one-liners for debugging. All calls are read-only. The API key is read from `FINNHUB_API_KEY` in the environment — it is defined in `.env` at the project root (`/Users/ivr/Documents/projects/refinery-pipeline/.env`), one level above the worktree.

**Rate limit:** 60 requests/minute on the free tier.

## Load the API key

Before running any snippet, load the key into the current shell:

```bash
set -a && source /Users/ivr/Documents/projects/refinery-pipeline/.env && set +a
```

## Available operations

Replace `GDX` with any ticker of interest.

### Company profile

```bash
python -c "
import os, json, finnhub
c = finnhub.Client(api_key=os.environ['FINNHUB_API_KEY'])
print(json.dumps(c.company_profile2(symbol='GDX'), indent=2))
"
```

### Recent news (last 7 days)

```bash
python -c "
import os, json, finnhub
from datetime import date, timedelta
c = finnhub.Client(api_key=os.environ['FINNHUB_API_KEY'])
today = date.today()
print(json.dumps(c.company_news('GDX', _from=str(today - timedelta(days=7)), to=str(today)), indent=2))
"
```

### Basic financials

```bash
python -c "
import os, json, finnhub
c = finnhub.Client(api_key=os.environ['FINNHUB_API_KEY'])
print(json.dumps(c.company_basic_financials('GDX', 'all'), indent=2))
"
```

### Symbol search

```bash
python -c "
import os, json, finnhub
c = finnhub.Client(api_key=os.environ['FINNHUB_API_KEY'])
print(json.dumps(c.symbol_search('gold'), indent=2))
"
```
````

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/finnhub-debug.md
git commit -m "chore(skills): add repo-scoped finnhub-debug skill"
```
