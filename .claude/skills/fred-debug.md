---
name: fred-debug
description: Read-only debugging access to the FRED API. Use to inspect macro series values, check data freshness, and print a full MacroSnapshot without running the full pipeline.
---

# FRED Debug Access

Use this skill to call FRED directly via Bash for debugging. All calls are read-only. The API key is read from `FRED_API_KEY` in `.env` at the project root.

**Rate limit:** 120 requests/minute on the free tier.

## Load the API key

Before running any snippet, load the key into the current shell:

```bash
set -a && source /Users/ivr/Documents/projects/refinery-pipeline/.env && set +a
```

## Available operations

### Fetch latest value for a single series

Replace `DFII10` with any series ID from `src/constants.py`.

```bash
uv run python -c "
import os
from datetime import date, timedelta
from fredapi import Fred
fred = Fred(api_key=os.environ['FRED_API_KEY'])
s = fred.get_series('DFII10', observation_start=date.today() - timedelta(days=30)).dropna()
print(f'Latest: {s.iloc[-1]:.4f} (as of {s.index[-1].date()})')
"
```

### Check freshness for all 8 tracked series

```bash
uv run python -c "
import os
from datetime import date, timedelta
from fredapi import Fred
from src.constants import (
    FRED_SERIES_DFII10, FRED_SERIES_T10YIE, FRED_SERIES_DTWEXBGS, FRED_SERIES_VIXCLS,
    FRED_SERIES_FEDFUNDS, FRED_SERIES_INDPRO, FRED_SERIES_CPIAUCSL, FRED_SERIES_WPU10,
    FRED_OBSERVATION_WINDOW_DAYS,
)
fred = Fred(api_key=os.environ['FRED_API_KEY'])
end = date.today()
start = end - timedelta(days=FRED_OBSERVATION_WINDOW_DAYS)
for sid in [FRED_SERIES_DFII10, FRED_SERIES_T10YIE, FRED_SERIES_DTWEXBGS, FRED_SERIES_VIXCLS,
            FRED_SERIES_FEDFUNDS, FRED_SERIES_INDPRO, FRED_SERIES_CPIAUCSL, FRED_SERIES_WPU10]:
    s = fred.get_series(sid, observation_start=start, observation_end=end).dropna()
    if s.empty:
        print(f'{sid:20s}  NO DATA')
    else:
        print(f'{sid:20s}  {s.iloc[-1]:10.4f}  (as of {s.index[-1].date()})')
"
```

### Print a full MacroSnapshot (all sections)

```bash
uv run python -c "
from src.config import get_settings
from src.integrations.fred import make_fred_client
client = make_fred_client(get_settings())
print(client.get_macro_snapshot().to_text())
"
```
