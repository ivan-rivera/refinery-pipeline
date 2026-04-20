---
name: peek-sheets
description: Read and surface Google Sheets tab contents so Claude can reason about live data. Use this skill whenever you need to inspect the current state of the test Google Sheet — for example, when debugging a Google Sheets integration, verifying that data was written correctly, checking what's in the universe/holdings/closed/learnings tabs, or understanding why a pipeline produced unexpected results. Trigger on any question about what data is in the sheet, discrepancies between expected and actual state, or when sheet context would help diagnose a problem.
---

# Peek Sheets

Reads a single tab from the project's test Google Sheet and prints its contents so you can reason about the live data.

## Available tabs

| Tab | Contents |
|---|---|
| `universe` | Watchlist of tracked tickers |
| `holdings` | Currently open positions |
| `closed` | Closed positions |
| `learnings` | Agent-generated trade learnings |

## Running the script

```bash
set -a && source .env && set +a
python .claude/skills/peek-sheets/scripts/read_tab.py <tab_name>
```

Example — inspect open positions:

```bash
set -a && source .env && set +a
python .claude/skills/peek-sheets/scripts/read_tab.py holdings
```

The script reads `GOOGLE_SHEET_ID_TEST` and `GOOGLE_CREDS_PATH` from the environment. The `source .env` step loads them from the project's `.env` file.

## Output format

The script prints the header row followed by all data rows, tab-separated. An empty tab prints only the header. Errors (missing env vars, unknown tab, auth failure) go to stderr with a clear message.

## Reading multiple tabs

If the problem involves relationships across tabs (e.g., a ticker in `holdings` that should also appear in `universe`), run the script once per relevant tab and compare the results side-by-side in your reasoning.
