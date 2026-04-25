"""Unit tests for the Edgar integration."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

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
