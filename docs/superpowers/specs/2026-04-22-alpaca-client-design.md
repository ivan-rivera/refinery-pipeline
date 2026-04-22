# Alpaca Client Integration — Design Spec

**Date:** 2026-04-22
**Status:** Approved
**Epic:** E3 — Market Connectivity

---

## 1. Scope

`AlpacaClient` is responsible for **execution and portfolio management only**. All market data (price history, volume, technicals) comes from Finnhub and TwelveData. The client surface is intentionally narrow: the five operations the trading pipeline actually needs, nothing more.

| Method | SDK call | Purpose |
|---|---|---|
| `get_account()` | `TradingClient.get_account()` | Portfolio equity and buying power for position sizing |
| `get_all_positions()` | `TradingClient.get_all_positions()` | Full portfolio review — list all open trades |
| `get_open_position(symbol)` | `TradingClient.get_open_position(symbol)` | Per-ticker position detail (same `Position` type, scoped to one symbol) |
| `close_position(symbol)` | `TradingClient.close_position(symbol)` | Exit expired trades |
| `submit_order(order_data)` | `TradingClient.submit_order(order_data)` | Place trades — callers construct the request |

Return types are alpaca-py's native types (`TradeAccount`, `Position`, `ClosePositionResponse`, `Order`). No translation layer. SDK types are intentionally allowed to leak into the trade execution component — that part of the pipeline is small and Alpaca-specific by nature. The research and analysis pipeline never touches this client.

Order construction is the caller's responsibility. The trade execution component will build `LimitOrderRequest` with `order_class=OrderClass.BRACKET`, `TakeProfitRequest`, and `StopLossRequest` directly, keeping bracket order assembly co-located with position sizing logic.

---

## 2. Paper vs Live

Paper or live trading is determined entirely by which API keys are configured — the codebase has no opinion on this. The `ALPACA_BASE_URL` environment variable sets the API endpoint and is passed to the SDK as `url_override`. No `paper=True/False` flag exists anywhere in the code.

Current `.env` state: both TEST and PROD point to `https://paper-api.alpaca.markets`. To go live with PROD, update `PROD_ALPACA_*` keys and `ALPACA_BASE_URL` in the environment. Zero code changes required.

---

## 3. Configuration

**New `Settings` fields** (added to `src/config.py`):

```python
alpaca_api_key_test:    str = Field(default="", alias="TEST_ALPACA_API_KEY")
alpaca_secret_key_test: str = Field(default="", alias="TEST_ALPACA_SECRET_KEY")
alpaca_api_key_prod:    str = Field(default="", alias="PROD_ALPACA_API_KEY")
alpaca_secret_key_prod: str = Field(default="", alias="PROD_ALPACA_SECRET_KEY")
alpaca_base_url:        str = Field(default="https://paper-api.alpaca.markets", alias="ALPACA_BASE_URL")
```

**New `Settings` helper method:**

```python
def alpaca_credentials(self, *, debug: bool) -> tuple[str, str]:
    """Return (api_key, secret_key) for the active environment."""
    if debug:
        return self.alpaca_api_key_test, self.alpaca_secret_key_test
    return self.alpaca_api_key_prod, self.alpaca_secret_key_prod
```

**`.env` change required:** the existing `ALPACA_BASE_URL=https://paper-api.alpaca.markets/v2` must be updated to `ALPACA_BASE_URL=https://paper-api.alpaca.markets` (drop the `/v2` suffix). The alpaca-py SDK appends version segments itself; passing `/v2` in `url_override` would produce malformed paths like `/v2/v2/account`.

---

## 4. File Structure

```
src/integrations/alpaca/
    __init__.py       # exports AlpacaClient, make_alpaca_client
    client.py         # AlpacaClient class + make_alpaca_client factory
```

Mirrors the existing `src/integrations/sheets/` layout exactly.

---

## 5. Client Design

```python
# src/integrations/alpaca/client.py

class AlpacaClient:
    def __init__(self, client: TradingClient) -> None:
        self._client = client

    def get_account(self) -> TradeAccount:
        return self._client.get_account()

    def get_all_positions(self) -> list[Position]:
        return self._client.get_all_positions()

    def get_open_position(self, symbol: str) -> Position:
        return self._client.get_open_position(symbol)

    def close_position(self, symbol: str) -> ClosePositionResponse:
        return self._client.close_position(symbol)

    def submit_order(self, order_data: OrderRequest) -> Order:
        return self._client.submit_order(order_data)


def make_alpaca_client(settings: Settings, *, debug: bool) -> AlpacaClient:
    api_key, secret_key = settings.alpaca_credentials(debug=debug)
    trading = TradingClient(api_key, secret_key, url_override=settings.alpaca_base_url)
    return AlpacaClient(trading)
```

No error wrapping. `APIError` from alpaca-py propagates to the call site, where the pipeline has the context to decide how to handle it. Wrapping here would suppress that context.

---

## 6. Testing

**File:** `tests/integrations/test_alpaca_client.py`

**Approach:** mock `TradingClient` at the boundary using `pytest-mock`. Tests verify:

- Each `AlpacaClient` method delegates to the correct `TradingClient` method
- Arguments pass through unchanged
- `make_alpaca_client` selects TEST credentials when `debug=True` and PROD credentials when `debug=False`
- `make_alpaca_client` passes `alpaca_base_url` as `url_override`

No integration tests against the live API. Interactive account inspection is handled by the `alpaca-mcp-server` MCP registered in Claude Code (using TEST paper keys).

---

## 7. Claude Code Alpaca Access

The `alpaca-mcp-server` MCP server is registered at user scope in Claude Code (`~/.claude.json`) using TEST paper account credentials. This gives Claude read access to account state, positions, and market data for debugging — without touching the PROD account. No custom skill or additional code is required in this repository.
