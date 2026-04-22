---
name: finnhub-debug
description: Read-only debugging access to the Finnhub API. Use to inspect company profiles, news, financials, and symbol search results without running the full pipeline.
---

# Finnhub Debug Access

Use this skill to call Finnhub directly via Bash one-liners for debugging. All calls are read-only. The API key is read from `FINNHUB_API_KEY` in the environment — it is defined in `.env` at the project root (`/Users/ivr/Documents/projects/refinery-pipeline/.env`), one level above the worktree.

**Rate limit:** 60 requests/minute on the free tier.

## Load the API key

Before running any snippet, load the key into the current shell:

```bash
set -a && source /Users/ivr/Documents/projects/refinery-pipeline/.env && set +a
```

## Available operations

Replace `GDX` with any ticker of interest.

### Company profile

```bash
python -c "
import os, json, finnhub
c = finnhub.Client(api_key=os.environ['FINNHUB_API_KEY'])
print(json.dumps(c.company_profile2(symbol='GDX'), indent=2))
"
```

### Recent news (last 7 days)

```bash
python -c "
import os, json, finnhub
from datetime import date, timedelta
c = finnhub.Client(api_key=os.environ['FINNHUB_API_KEY'])
today = date.today()
print(json.dumps(c.company_news('GDX', _from=str(today - timedelta(days=7)), to=str(today)), indent=2))
"
```

### Basic financials

```bash
python -c "
import os, json, finnhub
c = finnhub.Client(api_key=os.environ['FINNHUB_API_KEY'])
print(json.dumps(c.company_basic_financials('GDX', 'all'), indent=2))
"
```

### Symbol search

```bash
python -c "
import os, json, finnhub
c = finnhub.Client(api_key=os.environ['FINNHUB_API_KEY'])
print(json.dumps(c.symbol_lookup('gold'), indent=2))
"
```
