# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v0.4.0 (2026-04-23)

### Feat

- **alpaca**: add AlpacaClient and make_alpaca_client factory
- **config**: add Alpaca credential fields and alpaca_credentials helper

### Fix

- **lint**: resolve mypy and ruff issues in alpaca integration

## v0.3.0 (2026-04-20)

### Feat

- **schemas**: add ClosedPosition and Learning sheet row models

## v0.2.0 (2026-04-20)

### Feat

- **skills**: add peek-sheets skill for reading test Google Sheet tabs
- **sheets**: add Google Sheets connectivity for universe and holdings

### Fix

- **ci**: grant contents write permission to release workflow

### Refactor

- **sheets**: extract SheetRow base class and rename domain models
