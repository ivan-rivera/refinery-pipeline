"""Unit tests for the Edgar integration."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from src.integrations.edgar.client import EdgarClient, make_edgar_client
from src.schemas.edgar import (
    InsiderSummary,
    InsiderTransaction,
    InstitutionalHolder,
    InstitutionalSnapshot,
    MaterialEvent,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


# ---------------------------------------------------------------------------
# Schema construction
# ---------------------------------------------------------------------------


def test_insider_transaction_buy():
    tx = InsiderTransaction(
        filed_at=date(2026, 1, 15),
        insider_name="Jane Smith",
        position="CFO",
        is_buy=True,
        shares=10_000.0,
        price_per_share=25.50,
    )
    assert tx.is_buy is True
    assert tx.shares == 10_000.0


def test_insider_transaction_allows_null_price():
    tx = InsiderTransaction(
        filed_at=date(2026, 1, 15),
        insider_name="Jane Smith",
        position="CFO",
        is_buy=False,
        shares=5_000.0,
        price_per_share=None,
    )
    assert tx.price_per_share is None


def test_insider_summary_net_shares():
    summary = InsiderSummary(
        ticker="GOLD",
        period_days=90,
        net_shares=50_000.0,
        buy_count=3,
        sell_count=1,
        transactions=[],
    )
    assert summary.net_shares == 50_000.0
    assert summary.buy_count == 3


def test_institutional_holder_with_change():
    holder = InstitutionalHolder(
        fund_name="VAN ECK ASSOCIATES CORP",
        cik=869178,
        shares=5_000_000.0,
        value_usd=150_000.0,
        report_period="2025-Q4",
        prior_shares=4_000_000.0,
        change=1_000_000.0,
    )
    assert holder.change == 1_000_000.0


def test_institutional_holder_new_position():
    holder = InstitutionalHolder(
        fund_name="SPROTT INC.",
        cik=1512920,
        shares=2_000_000.0,
        value_usd=60_000.0,
        report_period="2025-Q4",
        prior_shares=None,
        change=None,
    )
    assert holder.prior_shares is None
    assert holder.change is None


def test_institutional_snapshot_aggregates():
    snapshot = InstitutionalSnapshot(
        ticker="NEM",
        report_period="2026-Q1",
        holders=[
            InstitutionalHolder(
                fund_name="Fund A",
                cik=1,
                shares=1_000_000.0,
                value_usd=30_000.0,
                report_period="2025-Q4",
                prior_shares=900_000.0,
                change=100_000.0,
            ),
            InstitutionalHolder(
                fund_name="Fund B",
                cik=2,
                shares=500_000.0,
                value_usd=15_000.0,
                report_period="2025-Q4",
                prior_shares=600_000.0,
                change=-100_000.0,
            ),
        ],
        total_institutional_shares=1_500_000.0,
        net_change_shares=0.0,
    )
    assert snapshot.total_institutional_shares == 1_500_000.0
    assert snapshot.net_change_shares == 0.0


def test_material_event_fields():
    event = MaterialEvent(
        filed_at=date(2026, 4, 20),
        item_codes=["2.02", "5.02"],
        description="Earnings Release, Officer/Director Change",
        url="https://www.sec.gov/Archives/edgar/data/123/000012320260001/form8k.htm",
    )
    assert "2.02" in event.item_codes
    assert event.filed_at == date(2026, 4, 20)


# ---------------------------------------------------------------------------
# get_insider_transactions
# ---------------------------------------------------------------------------


def test_get_insider_transactions_returns_buy_summary(mocker: MockerFixture) -> None:
    mock_form4 = mocker.MagicMock()
    mock_form4.get_net_shares_traded.return_value = 50_000
    mock_form4.insider_name = "Jane Smith"
    mock_form4.position = "CEO"

    mock_filing = mocker.MagicMock()
    mock_filing.filing_date = date(2026, 3, 1)
    mock_filing.obj.return_value = mock_form4

    mock_company = mocker.MagicMock()
    mock_company.get_filings.return_value = [mock_filing]
    mocker.patch("src.integrations.edgar.client.Company", return_value=mock_company)

    summary = EdgarClient().get_insider_transactions("GOLD", days=90)

    assert summary.ticker == "GOLD"
    assert summary.buy_count == 1
    assert summary.sell_count == 0
    assert summary.net_shares == 50_000.0
    assert summary.transactions[0].is_buy is True
    assert summary.transactions[0].insider_name == "Jane Smith"


def test_get_insider_transactions_returns_sell_summary(mocker: MockerFixture) -> None:
    mock_form4 = mocker.MagicMock()
    mock_form4.get_net_shares_traded.return_value = -20_000
    mock_form4.insider_name = "Bob Jones"
    mock_form4.position = "Director"

    mock_filing = mocker.MagicMock()
    mock_filing.filing_date = date(2026, 3, 15)
    mock_filing.obj.return_value = mock_form4

    mock_company = mocker.MagicMock()
    mock_company.get_filings.return_value = [mock_filing]
    mocker.patch("src.integrations.edgar.client.Company", return_value=mock_company)

    summary = EdgarClient().get_insider_transactions("NEM", days=90)

    assert summary.buy_count == 0
    assert summary.sell_count == 1
    assert summary.net_shares == -20_000.0
    assert summary.transactions[0].is_buy is False
    assert summary.transactions[0].shares == 20_000.0


def test_get_insider_transactions_skips_zero_net(mocker: MockerFixture) -> None:
    mock_form4 = mocker.MagicMock()
    mock_form4.get_net_shares_traded.return_value = 0
    mock_form4.insider_name = "Alice"
    mock_form4.position = "VP"

    mock_filing = mocker.MagicMock()
    mock_filing.filing_date = date(2026, 3, 1)
    mock_filing.obj.return_value = mock_form4

    mock_company = mocker.MagicMock()
    mock_company.get_filings.return_value = [mock_filing]
    mocker.patch("src.integrations.edgar.client.Company", return_value=mock_company)

    summary = EdgarClient().get_insider_transactions("GOLD", days=90)

    assert summary.buy_count == 0
    assert summary.sell_count == 0
    assert len(summary.transactions) == 0


def test_get_insider_transactions_skips_parse_errors(mocker: MockerFixture) -> None:
    mock_filing_bad = mocker.MagicMock()
    mock_filing_bad.filing_date = date(2026, 3, 1)
    mock_filing_bad.obj.side_effect = ValueError("parse failed")

    mock_form4 = mocker.MagicMock()
    mock_form4.get_net_shares_traded.return_value = 5_000
    mock_form4.insider_name = "Good Insider"
    mock_form4.position = "CFO"
    mock_filing_good = mocker.MagicMock()
    mock_filing_good.filing_date = date(2026, 3, 10)
    mock_filing_good.obj.return_value = mock_form4

    mock_company = mocker.MagicMock()
    mock_company.get_filings.return_value = [mock_filing_bad, mock_filing_good]
    mocker.patch("src.integrations.edgar.client.Company", return_value=mock_company)

    summary = EdgarClient().get_insider_transactions("GOLD", days=90)

    assert summary.buy_count == 1


def test_get_insider_transactions_empty_filings(mocker: MockerFixture) -> None:
    mock_company = mocker.MagicMock()
    mock_company.get_filings.return_value = []
    mocker.patch("src.integrations.edgar.client.Company", return_value=mock_company)

    summary = EdgarClient().get_insider_transactions("UNKN", days=90)

    assert summary.buy_count == 0
    assert summary.sell_count == 0
    assert summary.net_shares == 0.0


def test_make_edgar_client_calls_set_identity(mocker: MockerFixture) -> None:
    mock_set = mocker.patch("src.integrations.edgar.client.set_identity")
    settings = mocker.MagicMock()
    settings.edgar_identity = "Test User test@example.com"

    client = make_edgar_client(settings)

    mock_set.assert_called_once_with("Test User test@example.com")
    assert isinstance(client, EdgarClient)


def test_make_edgar_client_raises_when_identity_empty(mocker: MockerFixture) -> None:
    settings = mocker.MagicMock()
    settings.edgar_identity = ""

    with pytest.raises(ValueError, match="EDGAR_IDENTITY"):
        make_edgar_client(settings)


# ---------------------------------------------------------------------------
# get_material_events
# ---------------------------------------------------------------------------


def test_get_material_events_returns_recent_events(mocker: MockerFixture) -> None:
    from datetime import timedelta

    today = date.today()
    mock_filing = mocker.MagicMock()
    mock_filing.filing_date = today - timedelta(days=5)
    mock_filing.parsed_items = "2.02, 5.02"
    mock_filing.url = "https://www.sec.gov/Archives/edgar/data/123/form8k.htm"

    mock_company = mocker.MagicMock()
    mock_company.get_filings.return_value = [mock_filing]
    mocker.patch("src.integrations.edgar.client.Company", return_value=mock_company)

    events = EdgarClient().get_material_events("GOLD", days=30)

    assert len(events) == 1
    assert events[0].item_codes == ["2.02", "5.02"]
    assert events[0].description == "Earnings Release, Officer/Director Change"
    assert "sec.gov" in events[0].url


def test_get_material_events_handles_empty_items(mocker: MockerFixture) -> None:
    from datetime import timedelta

    today = date.today()
    mock_filing = mocker.MagicMock()
    mock_filing.filing_date = today - timedelta(days=2)
    mock_filing.parsed_items = ""
    mock_filing.url = "https://www.sec.gov/Archives/edgar/data/123/form8k.htm"

    mock_company = mocker.MagicMock()
    mock_company.get_filings.return_value = [mock_filing]
    mocker.patch("src.integrations.edgar.client.Company", return_value=mock_company)

    events = EdgarClient().get_material_events("GOLD", days=30)

    assert events[0].item_codes == []
    assert events[0].description == "Corporate Update"


def test_get_material_events_handles_no_filings(mocker: MockerFixture) -> None:
    mock_company = mocker.MagicMock()
    mock_company.get_filings.return_value = []
    mocker.patch("src.integrations.edgar.client.Company", return_value=mock_company)

    events = EdgarClient().get_material_events("UNKN", days=30)

    assert events == []


def test_get_material_events_passes_start_date_to_get_filings(mocker: MockerFixture) -> None:
    from datetime import timedelta

    mock_company = mocker.MagicMock()
    mock_company.get_filings.return_value = []
    mocker.patch("src.integrations.edgar.client.Company", return_value=mock_company)

    EdgarClient().get_material_events("GOLD", days=14)

    call_kwargs = mock_company.get_filings.call_args.kwargs
    expected_start = (date.today() - timedelta(days=14)).strftime("%Y-%m-%d")
    assert call_kwargs["start_date"] == expected_start
    assert call_kwargs["form"] == "8-K"


# ---------------------------------------------------------------------------
# get_institutional_holders + cache
# ---------------------------------------------------------------------------


def test_get_institutional_holders_reads_from_cache(mocker: MockerFixture, tmp_path: Path) -> None:
    cache_data = {
        "2026-Q2": {
            "GOLD": [
                {
                    "fund_name": "VAN ECK ASSOCIATES CORP",
                    "cik": 869178,
                    "shares": 5_000_000.0,
                    "value_usd": 150_000.0,
                    "report_period": "2025-12-31",
                    "prior_shares": 4_000_000.0,
                    "change": 1_000_000.0,
                }
            ]
        }
    }
    cache_file = tmp_path / "edgar_13f_cache.json"
    cache_file.write_text(json.dumps(cache_data))
    mocker.patch.object(EdgarClient, "_current_quarter", return_value="2026-Q2")

    snapshot = EdgarClient(cache_file=cache_file).get_institutional_holders("GOLD")

    assert snapshot.ticker == "GOLD"
    assert len(snapshot.holders) == 1
    assert snapshot.holders[0].fund_name == "VAN ECK ASSOCIATES CORP"
    assert snapshot.total_institutional_shares == 5_000_000.0
    assert snapshot.net_change_shares == 1_000_000.0


def test_get_institutional_holders_rebuilds_cache_on_quarter_miss(mocker: MockerFixture, tmp_path: Path) -> None:
    cache_file = tmp_path / "edgar_13f_cache.json"
    mocker.patch.object(EdgarClient, "_current_quarter", return_value="2026-Q2")
    mocker.patch.object(
        EdgarClient,
        "_build_quarterly_cache",
        return_value={
            "GOLD": [
                {
                    "fund_name": "SPROTT INC.",
                    "cik": 1512920,
                    "shares": 2_000_000.0,
                    "value_usd": 60_000.0,
                    "report_period": "2025-12-31",
                    "prior_shares": None,
                    "change": None,
                }
            ]
        },
    )

    snapshot = EdgarClient(cache_file=cache_file).get_institutional_holders("GOLD")

    assert len(snapshot.holders) == 1
    assert snapshot.holders[0].fund_name == "SPROTT INC."
    assert cache_file.exists()
    written = json.loads(cache_file.read_text())
    assert "2026-Q2" in written


def test_get_institutional_holders_does_not_rebuild_when_cache_current(mocker: MockerFixture, tmp_path: Path) -> None:
    cache_file = tmp_path / "edgar_13f_cache.json"
    cache_file.write_text(json.dumps({"2026-Q2": {}}))
    mocker.patch.object(EdgarClient, "_current_quarter", return_value="2026-Q2")
    build_mock = mocker.patch.object(EdgarClient, "_build_quarterly_cache")

    EdgarClient(cache_file=cache_file).get_institutional_holders("GOLD")

    build_mock.assert_not_called()


def test_get_institutional_holders_returns_empty_for_unheld_ticker(mocker: MockerFixture, tmp_path: Path) -> None:
    cache_file = tmp_path / "edgar_13f_cache.json"
    cache_file.write_text(json.dumps({"2026-Q2": {"NEM": []}}))
    mocker.patch.object(EdgarClient, "_current_quarter", return_value="2026-Q2")

    snapshot = EdgarClient(cache_file=cache_file).get_institutional_holders("UNKN")

    assert snapshot.ticker == "UNKN"
    assert len(snapshot.holders) == 0
    assert snapshot.total_institutional_shares == 0.0
    assert snapshot.net_change_shares == 0.0


def test_get_institutional_holders_ticker_lookup_is_case_insensitive(mocker: MockerFixture, tmp_path: Path) -> None:
    cache_data = {
        "2026-Q2": {
            "GOLD": [
                {
                    "fund_name": "VAN ECK ASSOCIATES CORP",
                    "cik": 869178,
                    "shares": 1_000_000.0,
                    "value_usd": 30_000.0,
                    "report_period": "2025-12-31",
                    "prior_shares": None,
                    "change": None,
                }
            ]
        }
    }
    cache_file = tmp_path / "edgar_13f_cache.json"
    cache_file.write_text(json.dumps(cache_data))
    mocker.patch.object(EdgarClient, "_current_quarter", return_value="2026-Q2")

    snapshot = EdgarClient(cache_file=cache_file).get_institutional_holders("gold")

    assert len(snapshot.holders) == 1
