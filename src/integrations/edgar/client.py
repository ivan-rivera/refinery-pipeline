"""Typed SEC EDGAR client.

Wraps edgartools so the rest of the codebase never imports from edgar.*
directly.  The 13F signal uses a curated list of institutional investor CIKs
that is fetched once per quarter and cached locally.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from edgar import Company, set_identity

from src.constants import (
    EDGAR_CACHE_FILE,
    EDGAR_INSTITUTIONAL_CIKS,
    EDGAR_THROTTLE_SECONDS,
)
from src.schemas.edgar import (
    InsiderSummary,
    InsiderTransaction,
    InstitutionalHolder,
    InstitutionalSnapshot,
    MaterialEvent,
)

if TYPE_CHECKING:
    from src.config import Settings

_logger = logging.getLogger(__name__)

_EDGAR_8K_ITEM_NAMES: dict[str, str] = {
    "1.01": "Material Agreement",
    "1.02": "Termination of Material Agreement",
    "1.03": "Bankruptcy/Receivership",
    "2.01": "Asset Acquisition/Disposition",
    "2.02": "Earnings Release",
    "2.03": "Direct Financial Obligation",
    "3.01": "Listing Standards",
    "4.01": "Auditor Change",
    "5.01": "Securities Act Registration",
    "5.02": "Officer/Director Change",
    "5.03": "Amendment to Articles",
    "7.01": "Press Release (Regulation FD)",
    "8.01": "Other Events",
    "9.01": "Financial Statements",
}


def _describe_8k_items(item_codes: list[str]) -> str:
    if not item_codes:
        return "Corporate Update"
    return ", ".join(_EDGAR_8K_ITEM_NAMES.get(code, code) for code in item_codes)


class EdgarClient:
    """Typed access to SEC EDGAR via edgartools."""

    def __init__(self, cache_file: Path = EDGAR_CACHE_FILE) -> None:
        self._cache_file = cache_file

    def get_insider_transactions(self, ticker: str, days: int = 90) -> InsiderSummary:
        """Return a summary of insider buy/sell activity for `ticker` over the last `days` days."""
        today = datetime.now(tz=UTC).date()
        filings = Company(ticker).get_filings(
            form="4",
            start_date=(today - timedelta(days=days)).strftime("%Y-%m-%d"),
            end_date=today.strftime("%Y-%m-%d"),
        )
        transactions: list[InsiderTransaction] = []
        for filing in filings:
            try:
                form4 = filing.obj()
                net = float(form4.get_net_shares_traded() or 0)
                if net == 0:
                    continue
                transactions.append(
                    InsiderTransaction(
                        filed_at=filing.filing_date,
                        insider_name=str(form4.insider_name or ""),
                        position=str(form4.position or ""),
                        is_buy=net > 0,
                        shares=abs(net),
                        price_per_share=None,
                    )
                )
            except Exception:
                _logger.warning("Skipping malformed Form 4 filing for %s", ticker, exc_info=True)
                continue

        buys = [t for t in transactions if t.is_buy]
        sells = [t for t in transactions if not t.is_buy]
        return InsiderSummary(
            ticker=ticker,
            period_days=days,
            net_shares=sum(t.shares for t in buys) - sum(t.shares for t in sells),
            buy_count=len(buys),
            sell_count=len(sells),
            transactions=transactions,
        )

    def get_material_events(self, ticker: str, days: int = 30) -> list[MaterialEvent]:
        """Return recent 8-K material events for `ticker` filed within the last `days` days."""
        cutoff = datetime.now(tz=UTC).date() - timedelta(days=days)
        filings = Company(ticker).get_filings(
            form="8-K",
            start_date=cutoff.strftime("%Y-%m-%d"),
        )
        events: list[MaterialEvent] = []
        for filing in filings:
            try:
                raw = filing.parsed_items or ""
                codes = [c.strip() for c in raw.split(",") if c.strip()]
                events.append(
                    MaterialEvent(
                        filed_at=filing.filing_date,
                        item_codes=codes,
                        description=_describe_8k_items(codes),
                        url=str(filing.url or ""),
                    )
                )
            except Exception:
                _logger.warning("Skipping malformed 8-K filing for %s", ticker, exc_info=True)
                continue
        return events

    def warm_cache(self) -> None:
        """Ensure the 13F quarterly cache is current, building it if needed (~10s on first call per quarter)."""
        quarter = self._current_quarter()
        cache = self._load_cache()
        if quarter not in cache:
            _logger.info("Building 13F quarterly cache for %s", quarter)
            cache[quarter] = self._build_quarterly_cache()
            self._save_cache(cache)
            _logger.info("13F cache built with %d tickers", len(cache[quarter]))

    def get_institutional_holders(self, ticker: str) -> InstitutionalSnapshot:
        """Return curated institutional holders of `ticker` from the most recent 13F cycle."""
        self.warm_cache()
        quarter = self._current_quarter()
        raw_holders = self._load_cache()[quarter].get(ticker.upper(), [])
        holders = [InstitutionalHolder(**h) for h in raw_holders]
        return InstitutionalSnapshot(
            ticker=ticker,
            report_period=quarter,
            holders=holders,
            total_institutional_shares=sum(h.shares for h in holders),
            net_change_shares=sum(h.change or 0.0 for h in holders),
        )

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    def _current_quarter(self) -> str:
        today = datetime.now(tz=UTC).date()
        q = (today.month - 1) // 3 + 1
        return f"{today.year}-Q{q}"

    def _load_cache(self) -> dict[str, dict[str, list[dict[str, Any]]]]:
        if not self._cache_file.exists():
            return {}
        with self._cache_file.open() as fh:
            return json.load(fh)

    def _save_cache(self, data: dict[str, dict[str, list[dict[str, Any]]]]) -> None:
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        with self._cache_file.open("w") as fh:
            json.dump(data, fh)

    def _build_quarterly_cache(self) -> dict[str, list[dict[str, Any]]]:
        """Fetch all curated funds' latest 13F holdings and invert by ticker."""
        inverted: dict[str, list[dict[str, Any]]] = {}

        for fund_name, cik in EDGAR_INSTITUTIONAL_CIKS.items():
            try:
                filing = Company(cik).get_filings(form="13F-HR").latest()
                if filing is None:
                    continue
                report = filing.obj()
                holdings_df = report.holdings
                if holdings_df is None or holdings_df.empty:
                    continue

                prev = report.previous_holding_report()
                prev_df = prev.holdings if prev is not None else None

                for _, row in holdings_df.iterrows():
                    ticker = str(row.get("Ticker", "") or "").upper()
                    if not ticker:
                        continue
                    shares = float(row.get("SharesPrnAmount", 0) or 0)
                    value = float(row.get("Value", 0) or 0)

                    prior_shares: float | None = None
                    change: float | None = None
                    if prev_df is not None and not prev_df.empty:
                        prev_rows = prev_df[prev_df["Ticker"] == ticker]
                        if not prev_rows.empty:
                            prior_shares = float(prev_rows.iloc[0].get("SharesPrnAmount", 0) or 0)
                            change = shares - prior_shares

                    inverted.setdefault(ticker, []).append(
                        {
                            "fund_name": fund_name,
                            "cik": cik,
                            "shares": shares,
                            "value_usd": value,
                            "report_period": str(report.report_period or ""),
                            "prior_shares": prior_shares,
                            "change": change,
                        }
                    )
            except Exception:
                _logger.warning("Skipping 13F fetch for fund CIK %s (%s)", cik, fund_name, exc_info=True)
                continue
            time.sleep(EDGAR_THROTTLE_SECONDS)

        return inverted


def make_edgar_client(settings: Settings) -> EdgarClient:
    """Build an EdgarClient from application settings."""
    if not settings.edgar_identity:
        raise ValueError("EDGAR_IDENTITY is not set")
    set_identity(settings.edgar_identity)
    client = EdgarClient()
    client.warm_cache()
    return client
