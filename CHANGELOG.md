# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v0.7.0 (2026-04-25)

### Feat

- **reddit**: add RedditClient with throttling and comment parsing
- **reddit**: add Comment and Thread schema models with to_text()

### Fix

- **ci**: exclude integration tests from just test and coverage recipes
- **reddit**: resolve lint errors and guard None body in _parse_comment

### Refactor

- **reddit**: replace magic kind/body strings with named constants
- **reddit**: move throttle interval to REDDIT_THROTTLE_SECONDS constant

## v0.6.0 (2026-04-23)

### Feat

- **integrations**: add FinnhubClient with typed response models
- **schemas**: add Finnhub typed response models

### Fix

- **integrations**: correct or-None coercion and dead fallback in FinnhubClient
- **schemas**: use AwareDatetime for NewsArticle.published_at

## v0.5.0 (2026-04-23)

### Feat

- **skills**: add project-level TwelveData debug skill
- **integrations**: add TwelveDataClient with OHLCV fetch
- **integrations**: add TwelveDataClient with OHLCV fetch
- **config**: add TWELVEDATA_API_KEY setting

### Fix

- **config**: add missing ignore_missing_imports to alpaca mypy override

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
