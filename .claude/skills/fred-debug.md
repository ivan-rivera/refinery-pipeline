---
name: fred-debug
description: Read-only debugging access to the FRED API. Use to inspect macro series values, check data freshness, and print a full MacroSnapshot without running the full pipeline.
---

# FRED Debug Access

All FRED access goes through `FredClient` in `src/integrations/fred/client.py`. Series IDs and the observation window are in `src/constants.py`. The API key is loaded from `FRED_API_KEY` via `src/config.py`.

To print a full snapshot:

```bash
uv run python -c "
from src.config import get_settings
from src.integrations.fred import make_fred_client
print(make_fred_client(get_settings()).get_macro_snapshot().to_text())
"
```

For ad-hoc inspection, instantiate `FredClient` directly and call `_fetch_series(series_id)` with any constant from `src/constants.py`.
