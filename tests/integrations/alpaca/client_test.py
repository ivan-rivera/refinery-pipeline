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
