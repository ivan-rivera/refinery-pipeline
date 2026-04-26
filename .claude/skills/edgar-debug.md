---
name: edgar-debug
description: Debugging guide for the SEC EDGAR integration. Use when inspecting insider transactions, institutional holders, or 8-K material events for a ticker, or when troubleshooting the 13F quarterly cache.
---

# Edgar Debug Access

All EDGAR access goes through `EdgarClient` in `src/integrations/edgar/client.py`. Read that file for current method signatures and return types — the schemas live in `src/schemas/edgar.py`.

## Setup

`EDGAR_IDENTITY` must be set in `.env` (format: `"Name email@example.com"`). Load it before running anything:

```bash
set -a && source "$(git rev-parse --show-toplevel)/.env" && set +a
```

Instantiate the client:

```python
from src.config import get_settings
from src.integrations.edgar import make_edgar_client

client = make_edgar_client(get_settings())  # also warms the 13F cache
```

## Methods

| Method | Form | Returns |
|---|---|---|
| `get_insider_transactions(ticker, days=90)` | 4 | `InsiderSummary` |
| `get_material_events(ticker, days=30)` | 8-K | `list[MaterialEvent]` |
| `get_institutional_holders(ticker)` | 13F-HR | `InstitutionalSnapshot` |

## 13F cache

The first call to `make_edgar_client` (or `client.warm_cache()`) fetches 13F filings from ~49 institutional investors and writes `data/cache/edgar_13f_cache.json`. This takes ~10s and happens once per fiscal quarter. To force a rebuild:

```bash
rm -f data/cache/edgar_13f_cache.json
```
