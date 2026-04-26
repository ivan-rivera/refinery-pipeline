# FRED Macro Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate FRED (Federal Reserve Economic Data) as a macro data source, delivering a typed `FredClient` / `MacroSnapshot` integration layer (PR 1) and pipeline wiring across the regime filter, scoring engine, and LLM research stage (PR 2).

**Architecture:** `FredClient` wraps `fredapi.Fred`, fetching 8 macro series per pipeline run and returning a single typed `MacroSnapshot(BaseModel)`. Downstream consumers receive `MacroSnapshot` as an explicit argument — no global state, no env coupling inside components. No caching: 8 daily fetches is negligible against FRED's 120 req/min limit. PR 1 delivers the integration layer; PR 2 wires it into the pipeline (execute once E6/E7/E8 stages are built).

**Tech Stack:** `fredapi>=0.5.1`, `pandas>=2.2.0` (already a dep), `pydantic>=2` (via pydantic-settings), `pytest-mock`

**FRED series tracked:**

| Series ID | Description | Frequency |
|-----------|-------------|-----------|
| `DFII10` | 10-Year TIPS Real Yield | Daily |
| `T10YIE` | 10-Year Breakeven Inflation Rate | Daily |
| `DTWEXBGS` | Nominal Broad USD Index | Daily |
| `VIXCLS` | CBOE VIX | Daily |
| `FEDFUNDS` | Effective Federal Funds Rate | Monthly |
| `INDPRO` | Industrial Production Index | Monthly |
| `CPIAUCSL` | CPI All Urban Consumers | Monthly |
| `WPU10` | PPI: Metals & Metal Products | Monthly |

---

## Agent Recommendation

**Both PRs suit a single agent each.** Multi-agent teams pay off when three or more workstreams are genuinely parallel with no shared state (e.g., building a frontend, backend, and test harness simultaneously). FRED has no such parallelism:

- **PR 1** is strictly sequential by type dependency: schema types must exist before the client that returns them, constants before either. One agent, one chain.
- **PR 2** has three integration points (regime filter, scoring, LLM), but each is a 5–15 line insertion into an existing function. The coordination overhead of parallel agents — context hand-off, potential merge conflicts in shared pipeline files — exceeds the time saved. One agent, one chain.

Dispatch a fresh agent per PR via `superpowers:subagent-driven-development`.

---

## PR 1: FRED Integration Layer

**Status: Ready to implement immediately.**

**Scope:** New integration, schema, config addition, constants, debug skill, and tests. No changes to pipeline logic.

### File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `src/integrations/fred/__init__.py` | Re-exports `make_fred_client` |
| Create | `src/integrations/fred/client.py` | `FredClient`, `_delta` helper, `make_fred_client` factory |
| Create | `src/schemas/fred.py` | `SeriesSnapshot`, `MacroSnapshot`, `_fmt` helper |
| Modify | `src/config.py` | Add `fred_api_key` field |
| Modify | `src/constants.py` | Add FRED series ID constants and `FRED_OBSERVATION_WINDOW_DAYS` |
| Modify | `pyproject.toml` | Add `fredapi>=0.5.1` to `[project] dependencies` |
| Modify | `pyproject.toml` | Add `[[tool.mypy.overrides]]` for `fredapi.*` |
| Create | `tests/integrations/fred_test.py` | Unit tests (mocked `fredapi.Fred`) |
| Create | `.claude/skills/fred-debug.md` | Debug skill |

---

### Task 1: Add `fredapi` dependency and `FRED_API_KEY` config field

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/config.py`

- [ ] **Step 1.1: Add `fredapi` to `pyproject.toml`**

In `pyproject.toml` under `[project]` → `dependencies`, append (maintaining alphabetical order):

```toml
"fredapi>=0.5.1",
```

After the last `[[tool.mypy.overrides]]` block (currently the `edgar.*` override), add:

```toml
[[tool.mypy.overrides]]
module = ["fredapi.*"]
ignore_missing_imports = true
```

- [ ] **Step 1.2: Install the dependency**

```bash
uv sync
```

Expected: lock file resolves `fredapi` with no conflicts. Verify with:

```bash
uv run python -c "from fredapi import Fred; print('OK')"
```

Expected: `OK`

- [ ] **Step 1.3: Add `fred_api_key` to `Settings` in `src/config.py`**

After the `finnhub_api_key` field:

```python
fred_api_key: str = Field(default="", alias="FRED_API_KEY")
```

- [ ] **Step 1.4: Verify the field loads from env**

```bash
uv run python -c "
import os; os.environ['FRED_API_KEY'] = 'smoke-test'
from src.config import Settings
s = Settings()
assert s.fred_api_key == 'smoke-test', s.fred_api_key
print('OK')
"
```

Expected: `OK`

- [ ] **Step 1.5: Run the existing test suite to confirm nothing regressed**

```bash
uv run pytest -q
```

Expected: all existing tests pass.

- [ ] **Step 1.6: Commit**

```bash
git add pyproject.toml src/config.py uv.lock
git commit -m "chore(fred): add fredapi dependency and FRED_API_KEY config field"
```

---

### Task 2: Add FRED constants

**Files:**
- Modify: `src/constants.py`

- [ ] **Step 2.1: Append FRED constants to `src/constants.py`**

```python
FRED_SERIES_DFII10 = "DFII10"          # 10-Year TIPS real yield (daily)
FRED_SERIES_T10YIE = "T10YIE"          # 10-Year breakeven inflation rate (daily)
FRED_SERIES_DTWEXBGS = "DTWEXBGS"      # Nominal broad USD index (daily)
FRED_SERIES_VIXCLS = "VIXCLS"          # CBOE VIX (daily)
FRED_SERIES_FEDFUNDS = "FEDFUNDS"      # Effective federal funds rate (monthly)
FRED_SERIES_INDPRO = "INDPRO"          # Industrial production index (monthly)
FRED_SERIES_CPIAUCSL = "CPIAUCSL"      # CPI all urban consumers (monthly)
FRED_SERIES_WPU10 = "WPU10"            # PPI metals & metal products (monthly)
FRED_OBSERVATION_WINDOW_DAYS = 60      # Calendar days of history fetched per series
```

- [ ] **Step 2.2: Commit**

```bash
git add src/constants.py
git commit -m "chore(fred): add FRED series ID constants"
```

---

### Task 3: Define `MacroSnapshot` schema

**Files:**
- Create: `src/schemas/fred.py`

- [ ] **Step 3.1: Create `src/schemas/fred.py`**

```python
"""FRED macro data schemas."""

from __future__ import annotations

from datetime import UTC, date, datetime

from pydantic import BaseModel


def _fmt(delta: float | None) -> str:
    return "N/A" if delta is None else f"{delta:+.2f}"


class SeriesSnapshot(BaseModel):
    """Latest value and short-term deltas for a single FRED series."""

    series_id: str
    latest_value: float
    latest_date: date
    delta_14d: float | None  # latest - value ≥14 calendar days ago; None if insufficient history
    delta_30d: float | None  # latest - value ≥30 calendar days ago; None if insufficient history


class MacroSnapshot(BaseModel):
    """Point-in-time snapshot of all tracked FRED macro series."""

    fetched_at: datetime
    real_yield_10y: SeriesSnapshot        # DFII10
    breakeven_inflation_10y: SeriesSnapshot  # T10YIE
    usd_broad_index: SeriesSnapshot       # DTWEXBGS
    vix: SeriesSnapshot                   # VIXCLS
    fed_funds_rate: SeriesSnapshot        # FEDFUNDS
    industrial_production: SeriesSnapshot  # INDPRO
    cpi: SeriesSnapshot                   # CPIAUCSL
    metals_ppi: SeriesSnapshot            # WPU10

    def to_text(self) -> str:
        """Serialise to plain text for injection into LLM agent context."""
        return "\n".join([
            f"Macro snapshot ({self.fetched_at.strftime('%Y-%m-%d')})",
            "",
            "--- Rates & Inflation ---",
            f"  Real 10Y yield (DFII10):        {self.real_yield_10y.latest_value:+.2f}%  Δ14d {_fmt(self.real_yield_10y.delta_14d)}pp",
            f"  10Y breakeven inflation:         {self.breakeven_inflation_10y.latest_value:.2f}%   Δ14d {_fmt(self.breakeven_inflation_10y.delta_14d)}pp",
            f"  Fed funds rate:                  {self.fed_funds_rate.latest_value:.2f}%   Δ30d {_fmt(self.fed_funds_rate.delta_30d)}pp",
            "",
            "--- Currency ---",
            f"  USD broad index (DTWEXBGS):      {self.usd_broad_index.latest_value:.2f}   Δ14d {_fmt(self.usd_broad_index.delta_14d)}",
            "",
            "--- Risk Regime ---",
            f"  VIX:                             {self.vix.latest_value:.2f}   Δ14d {_fmt(self.vix.delta_14d)}",
            "",
            "--- Activity & Prices ---",
            f"  Industrial production (INDPRO):  {self.industrial_production.latest_value:.2f}   Δ30d {_fmt(self.industrial_production.delta_30d)}",
            f"  CPI (CPIAUCSL):                  {self.cpi.latest_value:.2f}   Δ30d {_fmt(self.cpi.delta_30d)}",
            f"  Metals PPI (WPU10):              {self.metals_ppi.latest_value:.2f}   Δ30d {_fmt(self.metals_ppi.delta_30d)}",
        ])
```

- [ ] **Step 3.2: Smoke-check the schema imports cleanly**

```bash
uv run python -c "from src.schemas.fred import MacroSnapshot, SeriesSnapshot; print('OK')"
```

Expected: `OK`

- [ ] **Step 3.3: Commit**

```bash
git add src/schemas/fred.py
git commit -m "feat(fred): add SeriesSnapshot and MacroSnapshot schema with to_text()"
```

---

### Task 4: Implement `FredClient` (TDD)

**Files:**
- Create: `tests/integrations/fred_test.py`
- Create: `src/integrations/fred/client.py`
- Create: `src/integrations/fred/__init__.py`

- [ ] **Step 4.1: Write the failing tests first**

Create `tests/integrations/fred_test.py`:

```python
"""Unit tests for the FRED integration."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.integrations.fred.client import FredClient, make_fred_client
from src.schemas.fred import MacroSnapshot, SeriesSnapshot

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _daily_series(values: list[float]) -> pd.Series:
    """Build a daily pandas Series with the last value dated today."""
    end = date.today()
    start = end - timedelta(days=len(values) - 1)
    idx = pd.date_range(start=str(start), end=str(end), freq="D")
    return pd.Series(values[-len(idx) :], index=idx)


@pytest.fixture
def mock_fred() -> MagicMock:
    return MagicMock()


@pytest.fixture
def client(mock_fred: MagicMock) -> FredClient:
    return FredClient(mock_fred)


# ---------------------------------------------------------------------------
# get_macro_snapshot — return type
# ---------------------------------------------------------------------------


def test_get_macro_snapshot_returns_macro_snapshot(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.5] * 50)
    assert isinstance(client.get_macro_snapshot(), MacroSnapshot)


def test_get_macro_snapshot_all_series_fields_are_series_snapshots(
    client: FredClient, mock_fred: MagicMock
) -> None:
    mock_fred.get_series.return_value = _daily_series([2.0] * 50)
    result = client.get_macro_snapshot()
    for field in ("real_yield_10y", "breakeven_inflation_10y", "usd_broad_index", "vix",
                  "fed_funds_rate", "industrial_production", "cpi", "metals_ppi"):
        assert isinstance(getattr(result, field), SeriesSnapshot), f"Field {field!r} is not a SeriesSnapshot"


def test_get_macro_snapshot_fetches_all_eight_series(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.0] * 50)
    client.get_macro_snapshot()
    assert mock_fred.get_series.call_count == 8


# ---------------------------------------------------------------------------
# SeriesSnapshot values
# ---------------------------------------------------------------------------


def test_series_snapshot_latest_value_is_last_non_nan(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.0, 2.0, 3.0])
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.latest_value == pytest.approx(3.0)


def test_series_snapshot_latest_date_is_today(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.0] * 50)
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.latest_date == date.today()


def test_series_snapshot_delta_14d_computed_correctly(client: FredClient, mock_fred: MagicMock) -> None:
    """delta_14d = latest_value − value of the last observation ≥14 days ago."""
    values = [1.0] * 20 + [2.0] * 20
    mock_fred.get_series.return_value = _daily_series(values)
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.delta_14d == pytest.approx(1.0, abs=0.01)


def test_series_snapshot_delta_14d_is_none_when_insufficient_history(
    client: FredClient, mock_fred: MagicMock
) -> None:
    """delta_14d is None when the series has fewer than 15 data points."""
    mock_fred.get_series.return_value = _daily_series([1.0, 1.5, 2.0])
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.delta_14d is None


def test_series_snapshot_delta_30d_computed_correctly(client: FredClient, mock_fred: MagicMock) -> None:
    values = [1.0] * 35 + [3.0] * 10
    mock_fred.get_series.return_value = _daily_series(values)
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.delta_30d == pytest.approx(2.0, abs=0.01)


def test_series_snapshot_delta_30d_is_none_when_insufficient_history(
    client: FredClient, mock_fred: MagicMock
) -> None:
    mock_fred.get_series.return_value = _daily_series([1.0, 2.0])
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.delta_30d is None


def test_series_snapshot_nan_values_are_dropped(client: FredClient, mock_fred: MagicMock) -> None:
    import numpy as np
    s = _daily_series([1.0] * 48 + [np.nan, 3.0])
    mock_fred.get_series.return_value = s
    result = client.get_macro_snapshot()
    assert result.real_yield_10y.latest_value == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# make_fred_client
# ---------------------------------------------------------------------------


def test_make_fred_client_returns_fred_client(mocker: MockerFixture) -> None:
    mocker.patch("src.integrations.fred.client.Fred")
    settings = mocker.MagicMock()
    settings.fred_api_key = "test-key"
    assert isinstance(make_fred_client(settings), FredClient)


def test_make_fred_client_raises_when_key_is_empty(mocker: MockerFixture) -> None:
    settings = mocker.MagicMock()
    settings.fred_api_key = ""
    with pytest.raises(ValueError, match="FRED_API_KEY"):
        make_fred_client(settings)


# ---------------------------------------------------------------------------
# MacroSnapshot.to_text()
# ---------------------------------------------------------------------------


def test_to_text_contains_all_section_headers(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.5] * 50)
    text = client.get_macro_snapshot().to_text()
    for header in ("Rates & Inflation", "Currency", "Risk Regime", "Activity & Prices"):
        assert header in text, f"Missing section header: {header!r}"


def test_to_text_shows_na_when_delta_is_none(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([1.0, 2.0])
    text = client.get_macro_snapshot().to_text()
    assert "N/A" in text


def test_to_text_includes_series_values(client: FredClient, mock_fred: MagicMock) -> None:
    mock_fred.get_series.return_value = _daily_series([2.5] * 50)
    text = client.get_macro_snapshot().to_text()
    assert "2.50" in text
```

- [ ] **Step 4.2: Run the tests to confirm they all fail**

```bash
uv run pytest tests/integrations/fred_test.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.integrations.fred'` — all tests collected and failing.

- [ ] **Step 4.3: Create `src/integrations/fred/client.py`**

```python
"""Typed FRED (Federal Reserve Economic Data) client.

Wraps fredapi.Fred so the rest of the codebase never sees raw pandas or dicts.
Rate limit: 120 req/min on the free tier — irrelevant for a daily pipeline fetching 8 series.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

import pandas as pd
from fredapi import Fred

from src.constants import (
    FRED_OBSERVATION_WINDOW_DAYS,
    FRED_SERIES_CPIAUCSL,
    FRED_SERIES_DFII10,
    FRED_SERIES_DTWEXBGS,
    FRED_SERIES_FEDFUNDS,
    FRED_SERIES_INDPRO,
    FRED_SERIES_T10YIE,
    FRED_SERIES_VIXCLS,
    FRED_SERIES_WPU10,
)
from src.schemas.fred import MacroSnapshot, SeriesSnapshot

if TYPE_CHECKING:
    from src.config import Settings


def _delta(series: pd.Series, days: int) -> float | None:
    """Return (latest − value at or before `days` calendar days ago), or None."""
    cutoff = series.index[-1] - pd.Timedelta(days=days)
    past = series[series.index <= cutoff]
    if past.empty:
        return None
    return float(series.iloc[-1]) - float(past.iloc[-1])


class FredClient:
    """Typed access to FRED macro series."""

    def __init__(self, fred: Fred) -> None:
        self._fred = fred

    def _fetch_series(self, series_id: str) -> SeriesSnapshot:
        end = date.today()
        start = end - timedelta(days=FRED_OBSERVATION_WINDOW_DAYS)
        raw: pd.Series = self._fred.get_series(series_id, observation_start=start, observation_end=end)
        raw = raw.dropna()
        if raw.empty:
            raise ValueError(f"No observations returned for FRED series {series_id!r}")
        return SeriesSnapshot(
            series_id=series_id,
            latest_value=float(raw.iloc[-1]),
            latest_date=raw.index[-1].date(),
            delta_14d=_delta(raw, 14),
            delta_30d=_delta(raw, 30),
        )

    def get_macro_snapshot(self) -> MacroSnapshot:
        """Fetch all 8 tracked FRED series and return a typed MacroSnapshot."""
        return MacroSnapshot(
            fetched_at=datetime.now(UTC),
            real_yield_10y=self._fetch_series(FRED_SERIES_DFII10),
            breakeven_inflation_10y=self._fetch_series(FRED_SERIES_T10YIE),
            usd_broad_index=self._fetch_series(FRED_SERIES_DTWEXBGS),
            vix=self._fetch_series(FRED_SERIES_VIXCLS),
            fed_funds_rate=self._fetch_series(FRED_SERIES_FEDFUNDS),
            industrial_production=self._fetch_series(FRED_SERIES_INDPRO),
            cpi=self._fetch_series(FRED_SERIES_CPIAUCSL),
            metals_ppi=self._fetch_series(FRED_SERIES_WPU10),
        )


def make_fred_client(settings: Settings) -> FredClient:
    """Build a FredClient from application settings."""
    if not settings.fred_api_key:
        raise ValueError("FRED_API_KEY is not set")
    return FredClient(Fred(api_key=settings.fred_api_key))
```

- [ ] **Step 4.4: Create `src/integrations/fred/__init__.py`**

```python
"""FRED (Federal Reserve Economic Data) integration."""

from src.integrations.fred.client import make_fred_client

__all__ = ["make_fred_client"]
```

- [ ] **Step 4.5: Run the tests — confirm all pass**

```bash
uv run pytest tests/integrations/fred_test.py -v
```

Expected: all 14 tests pass.

- [ ] **Step 4.6: Run the full suite, linter, and type checker**

```bash
uv run pytest -q
uv run ruff check src/integrations/fred/ src/schemas/fred.py src/config.py src/constants.py
uv run mypy src/integrations/fred/ src/schemas/fred.py
```

Expected: all tests pass, no ruff violations, no mypy errors. (fredapi missing stubs are suppressed by the override added in Task 1.)

- [ ] **Step 4.7: Commit**

```bash
git add src/integrations/fred/ src/schemas/fred.py tests/integrations/fred_test.py
git commit -m "feat(fred): add FredClient, MacroSnapshot, and unit tests"
```

---

### Task 5: Write the FRED debug skill

**Files:**
- Create: `.claude/skills/fred-debug.md`

- [ ] **Step 5.1: Create `.claude/skills/fred-debug.md`**

```markdown
---
name: fred-debug
description: Read-only debugging access to the FRED API. Use to inspect macro series values, check data freshness, and print a full MacroSnapshot without running the full pipeline.
---

# FRED Debug Access

Use this skill to call FRED directly via Bash for debugging. All calls are read-only. The API key is read from `FRED_API_KEY` in `.env` at the project root.

**Rate limit:** 120 requests/minute on the free tier.

## Load the API key

Before running any snippet, load the key into the current shell:

```bash
set -a && source /Users/ivr/Documents/projects/refinery-pipeline/.env && set +a
```

## Available operations

### Fetch latest value for a single series

Replace `DFII10` with any series ID from `src/constants.py`.

```bash
uv run python -c "
import os
from datetime import date, timedelta
from fredapi import Fred
fred = Fred(api_key=os.environ['FRED_API_KEY'])
s = fred.get_series('DFII10', observation_start=date.today() - timedelta(days=30)).dropna()
print(f'Latest: {s.iloc[-1]:.4f} (as of {s.index[-1].date()})')
"
```

### Check freshness for all 8 tracked series

```bash
uv run python -c "
import os
from datetime import date, timedelta
from fredapi import Fred
from src.constants import (
    FRED_SERIES_DFII10, FRED_SERIES_T10YIE, FRED_SERIES_DTWEXBGS, FRED_SERIES_VIXCLS,
    FRED_SERIES_FEDFUNDS, FRED_SERIES_INDPRO, FRED_SERIES_CPIAUCSL, FRED_SERIES_WPU10,
    FRED_OBSERVATION_WINDOW_DAYS,
)
fred = Fred(api_key=os.environ['FRED_API_KEY'])
end = date.today()
start = end - timedelta(days=FRED_OBSERVATION_WINDOW_DAYS)
for sid in [FRED_SERIES_DFII10, FRED_SERIES_T10YIE, FRED_SERIES_DTWEXBGS, FRED_SERIES_VIXCLS,
            FRED_SERIES_FEDFUNDS, FRED_SERIES_INDPRO, FRED_SERIES_CPIAUCSL, FRED_SERIES_WPU10]:
    s = fred.get_series(sid, observation_start=start, observation_end=end).dropna()
    if s.empty:
        print(f'{sid:20s}  NO DATA')
    else:
        print(f'{sid:20s}  {s.iloc[-1]:10.4f}  (as of {s.index[-1].date()})')
"
```

### Print a full MacroSnapshot (all sections)

```bash
uv run python -c "
from src.config import get_settings
from src.integrations.fred import make_fred_client
client = make_fred_client(get_settings())
print(client.get_macro_snapshot().to_text())
"
```
```

- [ ] **Step 5.2: Run a quick lint pass on the skill file (YAML front-matter check)**

```bash
uv run python -c "
import re, pathlib
content = pathlib.Path('.claude/skills/fred-debug.md').read_text()
assert content.startswith('---'), 'Missing YAML front-matter'
print('OK')
"
```

Expected: `OK`

- [ ] **Step 5.3: Commit**

```bash
git add .claude/skills/fred-debug.md
git commit -m "docs(fred): add fred-debug Claude Code skill"
```

---

## PR 2: Pipeline Wiring

**Status: Blocked — implement once E6 (Stage 2 scoring), E7 (Stage 3 research agent), and E8 (regime filter) exist. This section is a wiring guide for the engineers building those stages, not a standalone workstream to execute now.**

Read `docs/project/ARCHITECTURE.md` sections 3.5–3.8 before starting.

### File Map

| Action | Path | What changes |
|--------|------|-------------|
| Modify | `src/pipelines/trade.py` | Call `make_fred_client`, fetch `MacroSnapshot` early in pipeline run |
| Modify | `src/components/regime/` *(E8)* | Accept `MacroSnapshot`; add three FRED-based regime gates |
| Modify | `src/components/score/` *(E6)* | Accept `MacroSnapshot`; add `real_yield_delta`, `breakeven_delta`, `metals_ppi_delta` score components |
| Modify | `src/components/agents/research/` *(E7)* | Inject `snapshot.to_text()` into the research agent system prompt |
| Modify | `tests/` for each above | Update or add tests for each new integration point |

---

### Task 1: Fetch `MacroSnapshot` in the pipeline entrypoint

**Files:**
- Modify: `src/pipelines/trade.py`

The `run` command already instantiates `settings`. Add the FRED client call immediately after and before any pipeline stage:

- [ ] **Step 1.1: Add the import and client call**

In `src/pipelines/trade.py`, add the import alongside the existing `make_sheets_client` import:

```python
from src.integrations.fred import make_fred_client
```

Inside the `run` command, after `settings = get_settings()`:

```python
fred_client = make_fred_client(settings)
macro_snapshot = fred_client.get_macro_snapshot()
console.print(f"  [dim]macro  :[/dim] FRED snapshot fetched ({macro_snapshot.fetched_at.strftime('%Y-%m-%d')})")
```

Pass `macro_snapshot` as an explicit argument to every stage function that consumes it (regime filter, scoring, research agent). Do not store it as a global or inject it via settings.

- [ ] **Step 1.2: Run the test suite**

```bash
uv run pytest -q
```

Expected: all tests pass. (The FRED call is mocked in unit tests; confirm no integration test tries to hit the network without the `integration` marker.)

- [ ] **Step 1.3: Commit**

```bash
git add src/pipelines/trade.py
git commit -m "feat(fred): fetch MacroSnapshot in pipeline entrypoint"
```

---

### Task 2: Regime Filter integration (E8)

**Files:**
- Modify: `src/components/regime/` (whichever file contains the regime coefficient function)
- Modify: the corresponding test file

The architecture (section 3.8) defines three regime gates for monetary metals plus one for copper. FRED contributes three additional gates that sit alongside the existing GDX/COPX/GDXJ logic.

- [ ] **Step 2.1: Write the failing tests for the three new FRED gates**

In the regime filter test file (e.g., `tests/components/regime_test.py`), add:

```python
from src.schemas.fred import MacroSnapshot, SeriesSnapshot
from datetime import date, datetime, UTC

def _snapshot(
    real_yield: float = 1.5,
    real_yield_delta_14d: float | None = -0.1,
    breakeven_delta_14d: float | None = 0.1,
    metals_ppi_delta_30d: float | None = 1.0,
    usd_delta_14d: float = 0.0,
    indpro_delta_30d: float | None = 1.0,
) -> MacroSnapshot:
    """Minimal MacroSnapshot fixture for regime and scoring tests.

    Place in tests/conftest.py or inline in each test module. All parameters
    default to values that represent a mild gold-bullish macro environment.
    """
    def _snap(series_id: str, value: float, d14: float | None = None, d30: float | None = None) -> SeriesSnapshot:
        return SeriesSnapshot(series_id=series_id, latest_value=value, latest_date=date.today(), delta_14d=d14, delta_30d=d30)
    return MacroSnapshot(
        fetched_at=datetime.now(UTC),
        real_yield_10y=_snap("DFII10", real_yield, d14=real_yield_delta_14d),
        breakeven_inflation_10y=_snap("T10YIE", 2.3, d14=breakeven_delta_14d),
        usd_broad_index=_snap("DTWEXBGS", 105.0, d14=usd_delta_14d),
        vix=_snap("VIXCLS", 18.0),
        fed_funds_rate=_snap("FEDFUNDS", 4.5),
        industrial_production=_snap("INDPRO", 103.0, d30=indpro_delta_30d),
        cpi=_snap("CPIAUCSL", 315.0),
        metals_ppi=_snap("WPU10", 220.0, d30=metals_ppi_delta_30d),
    )


def test_high_real_yield_caps_monetary_metal_budget(/* existing regime fn args */) -> None:
    """Real yield > 2.0% caps monetary metals risk budget at 50%."""
    snapshot = _snapshot(real_yield=2.5)
    result = compute_regime_coefficient(snapshot=snapshot, /* other args */)
    assert result.monetary_metal_budget_multiplier <= 0.5


def test_normal_real_yield_does_not_cap_monetary_metal_budget(/* existing regime fn args */) -> None:
    snapshot = _snapshot(real_yield=1.2)
    result = compute_regime_coefficient(snapshot=snapshot, /* other args */)
    assert result.monetary_metal_budget_multiplier == pytest.approx(1.0)


def test_rising_usd_adds_dollar_headwind_flag(/* existing regime fn args */) -> None:
    """USD broad index trending up (positive 14d delta) sets dollar_headwind=True."""
    snapshot = _snapshot(usd_delta_14d=2.5)
    result = compute_regime_coefficient(snapshot=snapshot, /* other args */)
    assert result.dollar_headwind is True


def test_falling_indpro_downgrades_copper_regime(/* existing regime fn args */) -> None:
    """Negative INDPRO 30d delta downgrades copper to Industrial Cautious."""
    snapshot = _snapshot(indpro_delta_30d=-0.8)
    result = compute_regime_coefficient(snapshot=snapshot, /* other args */)
    assert result.copper_regime == "industrial_cautious"
```

- [ ] **Step 2.2: Implement the three gates in the regime filter**

Add to `compute_regime_coefficient` (wherever the existing GDX/COPX/GDXJ logic lives):

```python
# --- FRED gate 1: real yield cap on monetary metals ---
REAL_YIELD_CAP_THRESHOLD = 2.0  # percentage points
if snapshot.real_yield_10y.latest_value > REAL_YIELD_CAP_THRESHOLD:
    monetary_metal_budget_multiplier = min(monetary_metal_budget_multiplier, 0.5)

# --- FRED gate 2: USD broad index trend ---
USD_HEADWIND_DELTA_THRESHOLD = 1.0  # index points over 14 calendar days
dollar_headwind = (
    snapshot.usd_broad_index.delta_14d is not None
    and snapshot.usd_broad_index.delta_14d > USD_HEADWIND_DELTA_THRESHOLD
)

# --- FRED gate 3: industrial production for copper ---
INDPRO_CONTRACTION_THRESHOLD = 0.0
if (
    snapshot.industrial_production.delta_30d is not None
    and snapshot.industrial_production.delta_30d < INDPRO_CONTRACTION_THRESHOLD
):
    copper_regime = "industrial_cautious"
```

Move the three threshold constants (`REAL_YIELD_CAP_THRESHOLD`, `USD_HEADWIND_DELTA_THRESHOLD`, `INDPRO_CONTRACTION_THRESHOLD`) to `src/constants.py` so they are operator-visible.

- [ ] **Step 2.3: Run tests and confirm all pass**

```bash
uv run pytest tests/components/regime_test.py -v
uv run pytest -q
```

- [ ] **Step 2.4: Commit**

```bash
git add src/components/regime/ src/constants.py tests/components/regime_test.py
git commit -m "feat(fred): wire MacroSnapshot into regime filter gates"
```

---

### Task 3: Stage 2 Scoring integration (E6)

**Files:**
- Modify: `src/components/score/` (whichever file contains the scoring function)
- Modify: the corresponding test file

Three FRED-derived components are added as normalized score signals in the monetary metals scoring path.

- [ ] **Step 3.1: Write the failing tests**

In the scoring test file (e.g., `tests/components/score_test.py`):

```python
from src.schemas.fred import MacroSnapshot, SeriesSnapshot
# reuse _snapshot() fixture from Task 2 or import from a conftest


def test_falling_real_yield_increases_score(base_candidate, baseline_snapshot) -> None:
    """Negative real_yield delta_14d should increase the monetary metals score."""
    snapshot_falling = _snapshot(real_yield_delta_14d=-0.5)
    snapshot_rising  = _snapshot(real_yield_delta_14d=+0.5)
    score_falling = compute_score(base_candidate, snapshot=snapshot_falling)
    score_rising  = compute_score(base_candidate, snapshot=snapshot_rising)
    assert score_falling > score_rising


def test_rising_breakeven_increases_score(base_candidate) -> None:
    """Positive breakeven delta_14d should increase the monetary metals score."""
    snap_up   = _snapshot(breakeven_delta_14d=+0.3)
    snap_down = _snapshot(breakeven_delta_14d=-0.3)
    assert compute_score(base_candidate, snapshot=snap_up) > compute_score(base_candidate, snapshot=snap_down)


def test_rising_metals_ppi_increases_producer_score(producer_candidate) -> None:
    """Positive metals_ppi delta_30d increases score for Producer business type."""
    snap_up   = _snapshot(metals_ppi_delta_30d=+3.0)
    snap_down = _snapshot(metals_ppi_delta_30d=-3.0)
    assert compute_score(producer_candidate, snapshot=snap_up) > compute_score(producer_candidate, snapshot=snap_down)


def test_none_deltas_do_not_raise(base_candidate) -> None:
    """None deltas (insufficient FRED history) are treated as neutral (0.0 contribution)."""
    snap = _snapshot(real_yield_delta_14d=None, breakeven_delta_14d=None, metals_ppi_delta_30d=None)
    score = compute_score(base_candidate, snapshot=snap)
    assert isinstance(score, float)
```

- [ ] **Step 3.2: Add the three FRED score components**

In the scoring function, after the existing signal calculations:

```python
# --- FRED macro signals (monetary metals) ---
REAL_YIELD_DELTA_CLIP = 1.0      # pp; changes beyond this are treated as max signal
BREAKEVEN_DELTA_CLIP = 0.5       # pp
METALS_PPI_DELTA_CLIP = 5.0      # index points

def _normalize(value: float | None, clip: float) -> float:
    """Clip to [-clip, clip] and normalize to [-1, 1]. None → 0 (neutral)."""
    if value is None:
        return 0.0
    return max(-1.0, min(1.0, value / clip))

# Falling real yields are bullish for monetary metals: negate the delta
real_yield_signal   = -_normalize(snapshot.real_yield_10y.delta_14d, REAL_YIELD_DELTA_CLIP)
breakeven_signal    = _normalize(snapshot.breakeven_inflation_10y.delta_14d, BREAKEVEN_DELTA_CLIP)
# Metals PPI only applied for Producer/Royalty/Developer business types
metals_ppi_signal   = (
    _normalize(snapshot.metals_ppi.delta_30d, METALS_PPI_DELTA_CLIP)
    if candidate.business_type in {"Producer", "Royalty", "Developer"}
    else 0.0
)

fred_score = (
    WEIGHT_REAL_YIELD   * real_yield_signal
    + WEIGHT_BREAKEVEN  * breakeven_signal
    + WEIGHT_METALS_PPI * metals_ppi_signal
)
```

Add the weight constants to `src/constants.py`:

```python
WEIGHT_REAL_YIELD = 0.15
WEIGHT_BREAKEVEN  = 0.10
WEIGHT_METALS_PPI = 0.05
```

Move `_normalize` to a shared scoring utilities module if one exists; otherwise define it at the top of the scoring file.

- [ ] **Step 3.3: Run tests**

```bash
uv run pytest tests/components/score_test.py -v
uv run pytest -q
```

- [ ] **Step 3.4: Commit**

```bash
git add src/components/score/ src/constants.py tests/components/score_test.py
git commit -m "feat(fred): add real_yield, breakeven, and metals_ppi scoring signals"
```

---

### Task 4: Stage 3 LLM research agent context injection (E7)

**Files:**
- Modify: `src/components/agents/research/` (whichever file constructs the research agent system prompt)
- Modify: the corresponding test file

- [ ] **Step 4.1: Write the failing test**

In the research agent test file (e.g., `tests/components/agents/research_test.py`):

```python
def test_system_prompt_includes_macro_snapshot(research_agent_deps_fixture) -> None:
    """The research agent system prompt must contain the macro snapshot text block."""
    snapshot = _snapshot()
    # Call the system prompt builder (or the agent's dynamic system prompt function)
    prompt_text = build_research_system_prompt(snapshot=snapshot, /* other args */)
    assert "Macro snapshot" in prompt_text
    assert "Real 10Y yield" in prompt_text


def test_system_prompt_macro_block_reflects_snapshot_values(research_agent_deps_fixture) -> None:
    snapshot = _snapshot(real_yield=3.14)
    prompt_text = build_research_system_prompt(snapshot=snapshot, /* other args */)
    assert "3.14" in prompt_text
```

- [ ] **Step 4.2: Inject `snapshot.to_text()` into the system prompt**

In the research agent module, wherever the system prompt string or dynamic system prompt function is defined:

```python
@agent.system_prompt(dynamic=True)
def research_system_prompt(ctx: RunContext[Deps]) -> str:
    macro_block = ctx.deps.macro_snapshot.to_text()
    return (
        "You are a precious metals equity research analyst.\n\n"
        f"{macro_block}\n\n"
        "Use the macro context above when forming your thesis. "
        "Highlight how the current rate, dollar, and inflation environment affects the candidate."
        # ... rest of existing system prompt ...
    )
```

`Deps` must include `macro_snapshot: MacroSnapshot`. Update the `Deps` dataclass accordingly.

- [ ] **Step 4.3: Run tests**

```bash
uv run pytest tests/components/agents/ -v
uv run pytest -q
```

- [ ] **Step 4.4: Commit**

```bash
git add src/components/agents/research/ tests/components/agents/
git commit -m "feat(fred): inject MacroSnapshot.to_text() into research agent system prompt"
```
