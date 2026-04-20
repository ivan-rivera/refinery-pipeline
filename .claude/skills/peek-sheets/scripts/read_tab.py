#!/usr/bin/env python3
# ruff: noqa: T201
"""Read a single tab from the test Google Sheet and print it to stdout."""

import os
import sys

import gspread

_KNOWN_TABS = {"universe", "holdings", "closed", "learnings"}


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <tab_name>", file=sys.stderr)
        print(f"Available tabs: {', '.join(sorted(_KNOWN_TABS))}", file=sys.stderr)
        sys.exit(1)

    tab = sys.argv[1]
    if tab not in _KNOWN_TABS:
        print(f"Unknown tab {tab!r}. Available: {', '.join(sorted(_KNOWN_TABS))}", file=sys.stderr)
        sys.exit(1)

    sheet_id = os.environ.get("GOOGLE_SHEET_ID_TEST")
    creds_path = os.environ.get("GOOGLE_CREDS_PATH")

    if not sheet_id:
        print("Error: GOOGLE_SHEET_ID_TEST is not set.", file=sys.stderr)
        sys.exit(1)
    if not creds_path:
        print("Error: GOOGLE_CREDS_PATH is not set.", file=sys.stderr)
        sys.exit(1)

    gc = gspread.service_account(filename=creds_path)
    spreadsheet = gc.open_by_key(sheet_id)
    ws = spreadsheet.worksheet(tab)
    rows = ws.get_all_values()

    if not rows:
        print(f"(tab '{tab}' is empty)")
        return

    for row in rows:
        print("\t".join(row))


if __name__ == "__main__":
    main()
