---
name: twelvedata-debug
description: Use when debugging TwelveData data issues — checking what price/volume history is available for a ticker, verifying OHLCV shape and date range, spot-checking the most recent close price, or confirming that a bad/delisted symbol is gracefully omitted from results.
---

# TwelveData Debug

Inspect what TwelveData returns for a symbol or set of symbols. Strictly read-only — no mutations.

## When to use

- Checking whether a ticker returns data at all
- Verifying OHLCV shape, date coverage, or data types
- Spot-checking the latest close or volume for a live ticker
- Confirming benchmarks (GDX, GDXJ, COPX, DXY) are reachable
- Verifying a delisted or invalid ticker is silently omitted

## How to query

Run any of the snippets below via Bash from the project root. The factory reads `TWELVEDATA_API_KEY` from `.env` automatically — no manual key handling needed.

### Fetch recent OHLCV for one or more tickers

```bash
python -c "
from src.config import Settings
from src.integrations.twelvedata.client import make_twelvedata_client

client = make_twelvedata_client(Settings())
data = client.get_ohlcv(['GDX', 'GLD'], outputsize=5)

for symbol, df in data.items():
    print(f'\n=== {symbol} ===')
    print(df.to_string())
"
```

### Check the most recent close price for a ticker

```bash
python -c "
from src.config import Settings
from src.integrations.twelvedata.client import make_twelvedata_client

client = make_twelvedata_client(Settings())
data = client.get_ohlcv(['GDX'], outputsize=1)

if 'GDX' in data:
    print('Latest close:', data['GDX']['close'].iloc[-1])
else:
    print('No data returned — symbol may be delisted or key invalid')
"
```

### Verify a bad ticker is silently omitted

```bash
python -c "
from src.config import Settings
from src.integrations.twelvedata.client import make_twelvedata_client

client = make_twelvedata_client(Settings())
data = client.get_ohlcv(['GDX', 'NOTAREALTICKER999'])

print('Symbols returned:', list(data.keys()))
# Expect: ['GDX'] only — bad ticker omitted, no exception raised
"
```

### Check all four benchmarks in one call

```bash
python -c "
from src.config import Settings
from src.integrations.twelvedata.client import make_twelvedata_client

BENCHMARKS = ['GDX', 'GDXJ', 'COPX', 'DXY']
client = make_twelvedata_client(Settings())
data = client.get_ohlcv(BENCHMARKS, outputsize=3)

for symbol in BENCHMARKS:
    if symbol in data:
        latest = data[symbol]['close'].iloc[-1]
        print(f'{symbol}: latest close = {latest:.4f}')
    else:
        print(f'{symbol}: NO DATA')
"
```

## Notes

- Run all commands from the **project root** so `.env` is discoverable
- `outputsize` = number of daily bars (default 100 ≈ 5 months)
- `interval` defaults to `"1day"` — pass `interval="1week"` for weekly bars
- Results are raw OHLCV only — no derived indicators (ATR, SMA, returns)
- A missing symbol is a warning in the logs, not an exception
