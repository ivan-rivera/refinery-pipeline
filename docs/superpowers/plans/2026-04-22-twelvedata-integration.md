# TwelveData Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a typed `TwelveDataClient` that fetches daily OHLCV bars for one or more symbols, extend `Settings` with the API key field, and add a project-level debugging skill.

**Architecture:** A thin typed facade (`TwelveDataClient`) wraps the official `twelvedata` SDK, following the same pattern as `SheetsClient` over `gspread`. A `make_twelvedata_client(settings)` factory is the single entry point. Pipeline stages receive `dict[str, pd.DataFrame]` and compute all derived indicators (ATR, SMA, returns) themselves from the raw OHLCV data.

**Tech Stack:** `twelvedata` (official Python SDK), `pandas` (DataFrame return type), `pytest-mock` (tests), `pydantic-settings` (config).

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `pyproject.toml` | Modify | Add `twelvedata` and `pandas` runtime dependencies; add mypy stub override |
| `src/config.py` | Modify | Add `twelvedata_api_key: str` field with `TWELVEDATA_API_KEY` alias |
| `src/integrations/twelvedata/__init__.py` | Create | Empty package marker |
| `src/integrations/twelvedata/client.py` | Create | `TwelveDataClient` class + `make_twelvedata_client` factory |
| `tests/integrations/twelvedata/__init__.py` | Create | Empty package marker |
| `tests/integrations/twelvedata/client_test.py` | Create | Unit tests (mocked SDK) |
| `.claude/skills/twelvedata-debug.md` | Create | Project-level debugging skill |

---

## Task 1: Add dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add `twelvedata` and `pandas` to runtime dependencies**

In `pyproject.toml`, update the `dependencies` list:

```toml
dependencies = [
    "click>=8.1.0",
    "rich>=14.0.0",
    "pydantic-settings>=2.13.0",
    "gspread>=6.1.0",
    "google-auth>=2.35.0",
    "twelvedata>=1.2.0",
    "pandas>=2.2.0",
]
```

- [ ] **Step 2: Add a mypy stub override for `twelvedata`**

The `twelvedata` package ships no type stubs. Add to `pyproject.toml` beneath the existing `[[tool.mypy.overrides]]` block:

```toml
[[tool.mypy.overrides]]
module = ["twelvedata.*", "pandas.*"]
ignore_missing_imports = true
```

- [ ] **Step 3: Install dependencies**

```bash
uv sync
```

Expected: no errors; `twelvedata` and `pandas` appear in the lock file.

- [ ] **Step 4: Verify installation**

```bash
python -c "from twelvedata import TDClient; import pandas as pd; print('ok')"
```

Expected output:
```
ok
```

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore(deps): add twelvedata and pandas dependencies"
```

---

## Task 2: Extend Settings with TwelveData API key

**Files:**
- Modify: `src/config.py`
- Modify: `tests/config_test.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/config_test.py`:

```python
def test_twelvedata_api_key_loaded_from_env() -> None:
    settings = Settings(_env_file=None, TWELVEDATA_API_KEY="td-test-key")
    assert settings.twelvedata_api_key == "td-test-key"


def test_twelvedata_api_key_defaults_to_empty() -> None:
    settings = Settings(_env_file=None)
    assert settings.twelvedata_api_key == ""
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
pytest tests/config_test.py::test_twelvedata_api_key_loaded_from_env tests/config_test.py::test_twelvedata_api_key_defaults_to_empty -v
```

Expected: both fail with `TypeError` or `ValidationError` (field doesn't exist yet).

- [ ] **Step 3: Add the field to Settings**

In `src/config.py`, add the new field to the `Settings` class after the existing `google_*` fields:

```python
twelvedata_api_key: str = Field(default="", alias="TWELVEDATA_API_KEY")
```

The full `Settings` class after the change:

```python
class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

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
    twelvedata_api_key: str = Field(default="", alias="TWELVEDATA_API_KEY")

    def sheet_id(self, *, debug: bool) -> str:
        """Return the Google Sheet id for the current environment."""
        return self.google_sheet_id_test if debug else self.google_sheet_id_prod
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
pytest tests/config_test.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/config.py tests/config_test.py
git commit -m "feat(config): add TWELVEDATA_API_KEY setting"
```

---

## Task 3: Implement TwelveDataClient

**Files:**
- Create: `src/integrations/twelvedata/__init__.py`
- Create: `src/integrations/twelvedata/client.py`
- Create: `tests/integrations/twelvedata/__init__.py`
- Create: `tests/integrations/twelvedata/client_test.py`

- [ ] **Step 1: Create the package markers**

Create `src/integrations/twelvedata/__init__.py` as an empty file.

Create `tests/integrations/twelvedata/__init__.py` as an empty file.

- [ ] **Step 2: Write the three failing tests**

Create `tests/integrations/twelvedata/client_test.py`:

```python
"""TwelveDataClient unit tests with a mocked twelvedata SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pytest
from src.config import Settings
from src.integrations.twelvedata.client import TwelveDataClient, make_twelvedata_client

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def _make_raw_df() -> pd.DataFrame:
    """Return a two-bar OHLCV DataFrame in descending order (newest first), as the SDK delivers."""
    return pd.DataFrame(
        {
            "open": [202.0, 201.0],
            "high": [206.0, 205.0],
            "low": [201.0, 200.0],
            "close": [204.0, 203.0],
            "volume": [1_200_000.0, 1_000_000.0],
        },
        index=pd.to_datetime(["2024-01-02", "2024-01-01"]),
    )


def test_get_ohlcv_returns_dataframe_per_symbol(mocker: MockerFixture) -> None:
    mock_td = mocker.patch("src.integrations.twelvedata.client.TDClient")
    mock_td.return_value.time_series.return_value.as_pandas.return_value = _make_raw_df()

    client = TwelveDataClient("test-key")
    result = client.get_ohlcv(["GDX", "GLD"])

    assert set(result.keys()) == {"GDX", "GLD"}
    for df in result.values():
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.is_monotonic_increasing
        assert all(df[col].dtype == float for col in df.columns)


def test_get_ohlcv_skips_symbol_on_error(mocker: MockerFixture) -> None:
    mock_td = mocker.patch("src.integrations.twelvedata.client.TDClient")

    def _ts_side_effect(symbol: str, **_kwargs: object) -> object:
        mock = mocker.MagicMock()
        if symbol == "INVALID":
            mock.as_pandas.side_effect = RuntimeError("symbol not found")
        else:
            mock.as_pandas.return_value = _make_raw_df()
        return mock

    mock_td.return_value.time_series.side_effect = _ts_side_effect

    client = TwelveDataClient("test-key")
    result = client.get_ohlcv(["GDX", "INVALID"])

    assert "GDX" in result
    assert "INVALID" not in result


def test_make_twelvedata_client_raises_for_missing_key() -> None:
    settings = Settings(_env_file=None)
    with pytest.raises(ValueError, match="TWELVEDATA_API_KEY"):
        make_twelvedata_client(settings)
```

- [ ] **Step 3: Run the tests to verify they fail**

```bash
pytest tests/integrations/twelvedata/client_test.py -v
```

Expected: all three tests fail with `ModuleNotFoundError` or `ImportError` (client module doesn't exist yet).

- [ ] **Step 4: Implement the client**

Create `src/integrations/twelvedata/client.py`:

```python
"""Typed client over the TwelveData API.

Wraps the official twelvedata SDK so the rest of the codebase
receives typed pandas DataFrames rather than raw SDK objects.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd
from twelvedata import TDClient

if TYPE_CHECKING:
    from src.config import Settings

_logger = logging.getLogger(__name__)


class TwelveDataClient:
    """Fetch OHLCV price/volume history from TwelveData."""

    def __init__(self, api_key: str) -> None:
        self._td = TDClient(apikey=api_key)

    def get_ohlcv(
        self,
        symbols: list[str],
        *,
        outputsize: int = 100,
        interval: str = "1day",
    ) -> dict[str, pd.DataFrame]:
        """Return split-adjusted OHLCV bars per symbol.

        Each DataFrame has columns open/high/low/close/volume (float64),
        indexed by DatetimeIndex sorted ascending. Symbols that produce
        an error are omitted from the result without raising.
        """
        results: dict[str, pd.DataFrame] = {}
        for symbol in symbols:
            try:
                df: pd.DataFrame = (
                    self._td.time_series(
                        symbol=symbol,
                        interval=interval,
                        outputsize=outputsize,
                        adjust="splits",
                    )
                    .as_pandas()
                )
            except Exception:
                _logger.warning("Failed to fetch OHLCV for %s", symbol, exc_info=True)
                continue
            if df is None or df.empty:
                _logger.warning("No data returned for %s", symbol)
                continue
            df = df.rename(columns=str.lower)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index(ascending=True)
            results[symbol] = df[["open", "high", "low", "close", "volume"]].astype(float)
        return results


def make_twelvedata_client(settings: Settings) -> TwelveDataClient:
    """Build a TwelveDataClient from application settings."""
    if not settings.twelvedata_api_key:
        raise ValueError("TWELVEDATA_API_KEY is not set")
    return TwelveDataClient(settings.twelvedata_api_key)
```

- [ ] **Step 5: Run the tests to verify they pass**

```bash
pytest tests/integrations/twelvedata/client_test.py -v
```

Expected: all three tests pass.

- [ ] **Step 6: Run the full test suite to catch regressions**

```bash
pytest
```

Expected: all tests pass, no regressions.

- [ ] **Step 7: Commit**

```bash
git add src/integrations/twelvedata/ tests/integrations/twelvedata/
git commit -m "feat(integrations): add TwelveDataClient with OHLCV fetch"
```

---

## Task 4: Add project-level debugging skill

**Files:**
- Create: `.claude/skills/twelvedata-debug.md`

- [ ] **Step 1: Create the skill file**

Create `.claude/skills/twelvedata-debug.md`:

```markdown
---
name: twelvedata-debug
description: Use when debugging TwelveData data issues — checking what price/volume history is available for a ticker, verifying OHLCV shape and date range, spot-checking the most recent close price, or confirming that a bad/delisted symbol is gracefully omitted from results.
---

# TwelveData Debug

Inspect what TwelveData returns for a symbol or set of symbols. Strictly read-only — no mutations.

## When to use

- Checking whether a ticker returns data at all
- Verifying OHLCV shape, date coverage, or data types
- Spot-checking the latest close or volume for a live ticker
- Confirming benchmarks (GDX, GDXJ, COPX, DXY) are reachable
- Verifying a delisted or invalid ticker is silently omitted

## How to query

Run any of the snippets below via Bash from the project root. The factory reads `TWELVEDATA_API_KEY` from `.env` automatically — no manual key handling needed.

### Fetch recent OHLCV for one or more tickers

```bash
python -c "
from src.config import Settings
from src.integrations.twelvedata.client import make_twelvedata_client

client = make_twelvedata_client(Settings())
data = client.get_ohlcv(['GDX', 'GLD'], outputsize=5)

for symbol, df in data.items():
    print(f'\n=== {symbol} ===')
    print(df.to_string())
"
```

### Check the most recent close price for a ticker

```bash
python -c "
from src.config import Settings
from src.integrations.twelvedata.client import make_twelvedata_client

client = make_twelvedata_client(Settings())
data = client.get_ohlcv(['GDX'], outputsize=1)

if 'GDX' in data:
    print('Latest close:', data['GDX']['close'].iloc[-1])
else:
    print('No data returned — symbol may be delisted or key invalid')
"
```

### Verify a bad ticker is silently omitted

```bash
python -c "
from src.config import Settings
from src.integrations.twelvedata.client import make_twelvedata_client

client = make_twelvedata_client(Settings())
data = client.get_ohlcv(['GDX', 'NOTAREALTICKER999'])

print('Symbols returned:', list(data.keys()))
# Expect: ['GDX'] only — bad ticker omitted, no exception raised
"
```

### Check all four benchmarks in one call

```bash
python -c "
from src.config import Settings
from src.integrations.twelvedata.client import make_twelvedata_client

BENCHMARKS = ['GDX', 'GDXJ', 'COPX', 'DXY']
client = make_twelvedata_client(Settings())
data = client.get_ohlcv(BENCHMARKS, outputsize=3)

for symbol in BENCHMARKS:
    if symbol in data:
        latest = data[symbol]['close'].iloc[-1]
        print(f'{symbol}: latest close = {latest:.4f}')
    else:
        print(f'{symbol}: NO DATA')
"
```

## Notes

- Run all commands from the **project root** so `.env` is discoverable
- `outputsize` = number of daily bars (default 100 ≈ 5 months)
- `interval` defaults to `"1day"` — pass `interval="1week"` for weekly bars
- Results are raw OHLCV only — no derived indicators (ATR, SMA, returns)
- A missing symbol is a warning in the logs, not an exception
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/twelvedata-debug.md
git commit -m "feat(skills): add project-level TwelveData debug skill"
```
