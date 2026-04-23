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
    """Build an AlpacaClient for the test or prod account."""
    api_key, secret_key = settings.alpaca_credentials(debug=debug)
    trading = TradingClient(api_key, secret_key, url_override=settings.alpaca_base_url)
    return AlpacaClient(trading)
