# Alpaca Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `AlpacaClient` — a thin wrapper over alpaca-py's `TradingClient` — for trade execution and portfolio management, plus the `Settings` fields that drive credential selection.

**Architecture:** `AlpacaClient` delegates directly to alpaca-py with no translation layer. `Settings` gains four credential fields and an `alpaca_credentials(debug)` helper. A `make_alpaca_client` factory wires them together, selecting TEST or PROD keys based on the `--debug` flag — identical pattern to `make_sheets_client`.

**Tech Stack:** `alpaca-py`, `pydantic-settings`, `pytest`, `pytest-mock`

> **Parallelism note:** Task 1 must complete before Tasks 2 and 3. Tasks 2 and 3 are independent and can run in parallel worktrees.

---

### Task 1: Add alpaca-py dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add the dependency**

In `pyproject.toml`, add `alpaca-py` to the `dependencies` list:

```toml
dependencies = [
    "click>=8.1.0",
    "rich>=14.0.0",
    "pydantic-settings>=2.13.0",
    "gspread>=6.1.0",
    "google-auth>=2.35.0",
    "alpaca-py>=0.38.0",
]
```

- [ ] **Step 2: Sync the environment**

```bash
uv sync
```

Expected: alpaca-py and its dependencies install without error.

- [ ] **Step 3: Verify import paths resolve**

```bash
python -c "from alpaca.trading.client import TradingClient; from alpaca.trading.models import TradeAccount, Position, Order; from alpaca.trading.requests import OrderRequest; print('OK')"
```

Expected: prints `OK`. If any import fails, adjust the import path — alpaca-py's internal layout can shift between minor versions. The model for `ClosePositionResponse` specifically may be at `alpaca.trading.models` or `alpaca.common.models`; check with:

```bash
python -c "import alpaca.trading.models as m; print([x for x in dir(m) if 'Close' in x])"
```

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore(deps): add alpaca-py"
```

---

### Task 2: Extend Settings with Alpaca credential fields

**Files:**
- Modify: `src/config.py`
- Modify: `tests/config_test.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/config_test.py`:

```python
def test_alpaca_credentials_returns_test_keys_in_debug() -> None:
    settings = Settings(_env_file=None, TEST_ALPACA_API_KEY="tkey", TEST_ALPACA_SECRET_KEY="tsecret")
    assert settings.alpaca_credentials(debug=True) == ("tkey", "tsecret")


def test_alpaca_credentials_returns_prod_keys_when_not_debug() -> None:
    settings = Settings(_env_file=None, PROD_ALPACA_API_KEY="pkey", PROD_ALPACA_SECRET_KEY="psecret")
    assert settings.alpaca_credentials(debug=False) == ("pkey", "psecret")
```

- [ ] **Step 2: Run to verify they fail**

```bash
pytest tests/config_test.py -v
```

Expected: both new tests FAIL with `TypeError` (unexpected keyword argument) or `AttributeError` (no `alpaca_credentials`).

- [ ] **Step 3: Implement the Settings fields and helper**

In `src/config.py`, add the five new fields and the helper method to the `Settings` class, after the existing Google fields:

```python
alpaca_api_key_test: str = Field(default="", alias="TEST_ALPACA_API_KEY")
alpaca_secret_key_test: str = Field(default="", alias="TEST_ALPACA_SECRET_KEY")
alpaca_api_key_prod: str = Field(default="", alias="PROD_ALPACA_API_KEY")
alpaca_secret_key_prod: str = Field(default="", alias="PROD_ALPACA_SECRET_KEY")
alpaca_base_url: str = Field(default="https://paper-api.alpaca.markets", alias="ALPACA_BASE_URL")

def alpaca_credentials(self, *, debug: bool) -> tuple[str, str]:
    """Return (api_key, secret_key) for the active environment."""
    if debug:
        return self.alpaca_api_key_test, self.alpaca_secret_key_test
    return self.alpaca_api_key_prod, self.alpaca_secret_key_prod
```

The full `Settings` class should look like this after the edit:

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

    alpaca_api_key_test: str = Field(default="", alias="TEST_ALPACA_API_KEY")
    alpaca_secret_key_test: str = Field(default="", alias="TEST_ALPACA_SECRET_KEY")
    alpaca_api_key_prod: str = Field(default="", alias="PROD_ALPACA_API_KEY")
    alpaca_secret_key_prod: str = Field(default="", alias="PROD_ALPACA_SECRET_KEY")
    alpaca_base_url: str = Field(default="https://paper-api.alpaca.markets", alias="ALPACA_BASE_URL")

    def sheet_id(self, *, debug: bool) -> str:
        """Return the Google Sheet id for the current environment."""
        return self.google_sheet_id_test if debug else self.google_sheet_id_prod

    def alpaca_credentials(self, *, debug: bool) -> tuple[str, str]:
        """Return (api_key, secret_key) for the active environment."""
        if debug:
            return self.alpaca_api_key_test, self.alpaca_secret_key_test
        return self.alpaca_api_key_prod, self.alpaca_secret_key_prod
```

- [ ] **Step 4: Run the tests to verify they pass**

```bash
pytest tests/config_test.py -v
```

Expected: all tests PASS, including the two new ones.

- [ ] **Step 5: Commit**

```bash
git add src/config.py tests/config_test.py
git commit -m "feat(config): add Alpaca credential fields and alpaca_credentials helper"
```

---

### Task 3: Implement AlpacaClient and factory

**Files:**
- Create: `src/integrations/alpaca/__init__.py`
- Create: `src/integrations/alpaca/client.py`
- Create: `tests/integrations/alpaca/__init__.py`
- Create: `tests/integrations/alpaca/client_test.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/integrations/alpaca/__init__.py` (empty):

```python
```

Create `tests/integrations/alpaca/client_test.py`:

```python
"""AlpacaClient delegation tests with a mocked TradingClient."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.integrations.alpaca.client import AlpacaClient, make_alpaca_client

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


def _make_client(mocker: MockerFixture) -> tuple[AlpacaClient, object]:
    mock_trading = mocker.MagicMock(name="trading_client")
    return AlpacaClient(mock_trading), mock_trading


def test_get_account_delegates(mocker: MockerFixture) -> None:
    client, mock_trading = _make_client(mocker)
    result = client.get_account()
    mock_trading.get_account.assert_called_once_with()
    assert result is mock_trading.get_account.return_value


def test_get_all_positions_delegates(mocker: MockerFixture) -> None:
    client, mock_trading = _make_client(mocker)
    result = client.get_all_positions()
    mock_trading.get_all_positions.assert_called_once_with()
    assert result is mock_trading.get_all_positions.return_value


def test_get_open_position_delegates(mocker: MockerFixture) -> None:
    client, mock_trading = _make_client(mocker)
    result = client.get_open_position("GDX")
    mock_trading.get_open_position.assert_called_once_with("GDX")
    assert result is mock_trading.get_open_position.return_value


def test_close_position_delegates(mocker: MockerFixture) -> None:
    client, mock_trading = _make_client(mocker)
    result = client.close_position("NEM")
    mock_trading.close_position.assert_called_once_with("NEM")
    assert result is mock_trading.close_position.return_value


def test_submit_order_delegates(mocker: MockerFixture) -> None:
    client, mock_trading = _make_client(mocker)
    order_data = mocker.MagicMock(name="order_request")
    result = client.submit_order(order_data)
    mock_trading.submit_order.assert_called_once_with(order_data)
    assert result is mock_trading.submit_order.return_value


def test_make_alpaca_client_uses_debug_credentials(mocker: MockerFixture) -> None:
    mock_settings = mocker.MagicMock()
    mock_settings.alpaca_credentials.return_value = ("tkey", "tsecret")
    mock_settings.alpaca_base_url = "https://paper-api.alpaca.markets"
    mocker.patch("src.integrations.alpaca.client.TradingClient")

    make_alpaca_client(mock_settings, debug=True)

    mock_settings.alpaca_credentials.assert_called_once_with(debug=True)


def test_make_alpaca_client_uses_prod_credentials(mocker: MockerFixture) -> None:
    mock_settings = mocker.MagicMock()
    mock_settings.alpaca_credentials.return_value = ("pkey", "psecret")
    mock_settings.alpaca_base_url = "https://paper-api.alpaca.markets"
    mocker.patch("src.integrations.alpaca.client.TradingClient")

    make_alpaca_client(mock_settings, debug=False)

    mock_settings.alpaca_credentials.assert_called_once_with(debug=False)


def test_make_alpaca_client_passes_url_override(mocker: MockerFixture) -> None:
    mock_settings = mocker.MagicMock()
    mock_settings.alpaca_credentials.return_value = ("k", "s")
    mock_settings.alpaca_base_url = "https://paper-api.alpaca.markets"
    mock_ctor = mocker.patch("src.integrations.alpaca.client.TradingClient")

    make_alpaca_client(mock_settings, debug=True)

    mock_ctor.assert_called_once_with("k", "s", url_override="https://paper-api.alpaca.markets")
```

- [ ] **Step 2: Run to verify the tests fail**

```bash
pytest tests/integrations/alpaca/client_test.py -v
```

Expected: all tests FAIL with `ModuleNotFoundError: No module named 'src.integrations.alpaca'`.

- [ ] **Step 3: Create the integration module files**

Create `src/integrations/alpaca/__init__.py`:

```python
from src.integrations.alpaca.client import AlpacaClient, make_alpaca_client

__all__ = ["AlpacaClient", "make_alpaca_client"]
```

Create `src/integrations/alpaca/client.py`:

> **Note:** Run `python -c "from alpaca.trading.models import ClosePositionResponse"` first. If it raises `ImportError`, check the correct module with `python -c "import alpaca.trading.models as m; print(dir(m))"` and substitute the right path below.

```python
"""Thin wrapper over alpaca-py TradingClient for execution and portfolio queries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from alpaca.trading.client import TradingClient
from alpaca.trading.models import ClosePositionResponse, Order, Position, TradeAccount
from alpaca.trading.requests import OrderRequest

if TYPE_CHECKING:
    from src.config import Settings


class AlpacaClient:
    """Typed access to Alpaca trade execution and portfolio management."""

    def __init__(self, client: TradingClient) -> None:
        self._client = client

    def get_account(self) -> TradeAccount:
        return self._client.get_account()  # type: ignore[return-value]

    def get_all_positions(self) -> list[Position]:
        return self._client.get_all_positions()  # type: ignore[return-value]

    def get_open_position(self, symbol: str) -> Position:
        return self._client.get_open_position(symbol)  # type: ignore[return-value]

    def close_position(self, symbol: str) -> ClosePositionResponse:
        return self._client.close_position(symbol)  # type: ignore[return-value]

    def submit_order(self, order_data: OrderRequest) -> Order:
        return self._client.submit_order(order_data)  # type: ignore[return-value]


def make_alpaca_client(settings: Settings, *, debug: bool) -> AlpacaClient:
    """Build an AlpacaClient for the test or prod account."""
    api_key, secret_key = settings.alpaca_credentials(debug=debug)
    trading = TradingClient(api_key, secret_key, url_override=settings.alpaca_base_url)
    return AlpacaClient(trading)
```

> **On the `# type: ignore[return-value]` comments:** alpaca-py's `TradingClient` is not fully typed — its methods return `Any` or `dict` in stubs. These ignores suppress mypy noise caused by the SDK's incomplete annotations, not by our code. Remove them if a future alpaca-py release ships proper stubs.

- [ ] **Step 4: Run the tests to verify they pass**

```bash
pytest tests/integrations/alpaca/client_test.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Run the full test suite to check for regressions**

```bash
pytest
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/integrations/alpaca/ tests/integrations/alpaca/
git commit -m "feat(alpaca): add AlpacaClient and make_alpaca_client factory"
```
