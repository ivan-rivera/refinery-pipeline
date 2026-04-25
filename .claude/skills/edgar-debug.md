---
name: edgar-debug
description: Read-only debugging access to SEC EDGAR via EdgarClient. Use to inspect insider transactions, institutional holders, and 8-K material events for any ticker without running the full pipeline. Requires EDGAR_IDENTITY in the environment.
---

# Edgar Debug Access

Inspect EDGAR data using the project's `EdgarClient`. All calls are read-only. `EDGAR_IDENTITY` must be set in `.env` at the project root.

Run all commands from the worktree root with `uv run python -c "..."`.

---

## Load the identity

Before running any snippet, load the env (from the project root):

```bash
set -a && source "$(git rev-parse --show-toplevel)/.env" && set +a
```

Verify identity is set:

```bash
echo $EDGAR_IDENTITY
```

Expected: `Ivan Rivera ivan.s.rivera@gmail.com` (or whatever is configured).

---

## Insider transactions (Form 4)

Returns net insider buy/sell activity for a ticker over the last 90 days.

```bash
uv run python -c "
from src.config import get_settings
from src.integrations.edgar import make_edgar_client

client = make_edgar_client(get_settings())
summary = client.get_insider_transactions('NEM', days=90)

print(f'Ticker: {summary.ticker}  Period: {summary.period_days}d')
print(f'Net shares: {summary.net_shares:+,.0f}  Buys: {summary.buy_count}  Sells: {summary.sell_count}')
for tx in summary.transactions[:5]:
    direction = 'BUY ' if tx.is_buy else 'SELL'
    print(f'  [{direction}] {tx.filed_at}  {tx.insider_name} ({tx.position})  {tx.shares:,.0f} shares')
"
```

---

## Institutional holders (13F)

Returns the curated institutional holders of a ticker. **First call per quarter triggers a rebuild (~10s); subsequent calls are instant from cache.**

```bash
uv run python -c "
from src.config import get_settings
from src.integrations.edgar import make_edgar_client

client = make_edgar_client(get_settings())
snapshot = client.get_institutional_holders('GOLD')

print(f'Ticker: {snapshot.ticker}  Period: {snapshot.report_period}')
print(f'Total shares: {snapshot.total_institutional_shares:,.0f}')
print(f'Net change:   {snapshot.net_change_shares:+,.0f}')
print()
for h in sorted(snapshot.holders, key=lambda x: x.shares, reverse=True)[:10]:
    chg = f'{h.change:+,.0f}' if h.change is not None else 'NEW'
    print(f'  {h.fund_name[:40]:40s}  {h.shares:>15,.0f}  ({chg})')
"
```

---

## Material events (8-K)

Returns recent corporate events filed in the last 30 days.

```bash
uv run python -c "
from src.config import get_settings
from src.integrations.edgar import make_edgar_client

client = make_edgar_client(get_settings())
events = client.get_material_events('NEM', days=30)

if not events:
    print('No 8-K events in the last 30 days')
else:
    for e in events:
        print(f'[{e.filed_at}] {e.description}')
        print(f'  Items: {e.item_codes}')
        print(f'  URL:   {e.url}')
        print()
"
```

---

## Cache location

The 13F quarterly cache is stored at `data/cache/edgar_13f_cache.json` (gitignored).
To force a rebuild (e.g. after adding a new fund to `EDGAR_INSTITUTIONAL_CIKS`):

```bash
rm -f data/cache/edgar_13f_cache.json
```

The next call to `get_institutional_holders` will automatically rebuild it.

---

## Notes

- **No API key** — only `EDGAR_IDENTITY` (name + email) is required as a User-Agent
- **Rate limit**: SEC EDGAR allows ≤10 req/s; 13F rebuild sleeps 0.2s between funds (~10s total)
- **13F cache**: quarterly TTL — rebuilds once per fiscal quarter automatically
- **Form 4 / 8-K**: no caching — fetched fresh each call; one HTTP request per ticker
