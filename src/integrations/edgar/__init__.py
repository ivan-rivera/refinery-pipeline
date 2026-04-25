"""SEC EDGAR integration."""

from src.integrations.edgar.client import EdgarClient, make_edgar_client

__all__ = ["EdgarClient", "make_edgar_client"]
