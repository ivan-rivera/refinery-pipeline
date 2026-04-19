# Architecture

This document outlines the design, mechanics, and operational principles of an autonomous swing trading system focused on precious metals equities.

---

## 1. Overview

The system is designed to operate as a **daily pipeline** executing a fully automated trading workflow for swing trades (5–28 day horizon) across:

* NYSE
* NYSE Arca
* NASDAQ

The system prioritizes:

* Deterministic decision-making over heuristic judgment
* Strict risk management and capital preservation
* Iterative improvement via structured data collection

---

## 2. Core Design Principles

1. **Deterministic Decisions**
   All trade decisions are driven by a scoring function and rule-based constraints. LLMs are used for summarization and augmentation, not decision-making.

2. **Risk-First Architecture**
   Portfolio-level and trade-level risk constraints take precedence over opportunity selection.

3. **Selective Complexity**
   Expensive or complex analysis is only applied to a small subset of high-potential candidates.

4. **Structured Learning**
   All trades and outcomes are stored as structured data to enable analysis and system improvement.

5. **Observability**
   Every decision is logged with both human-readable and machine-readable context.

---

## 3. Pipeline Structure

The pipeline runs on a scheduled daily basis and consists of the following stages:

---

### 3.1 Universe Refresh (Periodic)

A separate pipeline maintains a whitelist of eligible tickers (~200–300), filtered by:

* Precious metals exposure (gold, silver, copper)
* Minimum market cap
* Minimum average volume
* Exchange eligibility

Tickers are categorized by:

* Metal exposure
* Business type (Producer, Developer, Explorer, Royalty/Streamer)

---

### 3.2 Portfolio Review

If active positions exist, the system evaluates:

#### a) Exit Conditions

Positions are closed if any of the following are met:

* Stop-loss triggered
* Take-profit reached
* Thesis expiry reached

Stop-loss and take-profit triggers should be executed automatically by the trading system, whereas the expiry condition will require the system to place a trade.

#### b) Trade Logging

For each closed trade, the system records:

* Entry features and signals
* Exit outcome (% return, duration)
* Exit reason

These metrics should already be available in the trading platform, however, we also want to add a learning from that trade -- did our thesis materialise? If not, why could that be? What could we do differently next time?

#### c) Learning Capture

As seen earlier, closed positions generate learnings per trade, these learnings will be batched in groups of N (configurable, the default could be 10) and these batches will be aggregated into global-level learnings that LLMs will use to propose future trade-level score multipliers

---

### 3.3 Risk Budget Check

Before entering new trades:

* Calculate total deployed risk across open positions
* Enforce:

  * Max risk per trade (e.g. 2.5%)
  * Max total portfolio risk, i.e. the sum of all worst case losses (e.g. 10%)

If risk budget is exhausted:
→ No new trades are opened

---

### 3.4 Candidate Generation

Candidate tickers are sourced from:

* Predefined screeners
* Market data APIs
* News and social sentiment sources

---

### 3.5 Stage 1: Quantitative Filtering

Apply fast, deterministic filters to reduce candidate pool:

* Average daily volume > 500K
* Price > 2
* Price > 50d MA
* Daily volatility between 0.02 and 0.08
* Return (14d) > GDX return (14d)
* Top N momentum (e.g. top 20 by 14d return)
* Volume spike (e.g. > 2x 20d avg)
* Breakout (price > 50d high)
* Relative strength vs GDX
* Relative strength vs DXY
* Correlations with open positions

Output: Top ~20 candidates

---

### 3.6 Stage 2: Scoring & Ranking

Each candidate is scored using a weighted function:

Example components:

* Momentum
* Relative strength
* Volume anomalies
* Sentiment signals
* Volatility penalty
* Jurisdiction risk penalty

All features are normalized.

Output:

* Ranked list of candidates

---

### 3.7 Stage 3: Deep Research (Top N)

Top ~5–10 candidates undergo deeper analysis:

* News summarization
* Catalyst detection
* Sentiment validation
* Risk flag identification

LLMs may be used in this stage to:

* Summarize information
* Highlight key narratives
* Extract structured insights

Outputs are converted into structured features and fed back into scoring.

---

### 3.8 Regime Filter

Before trade execution, apply macro-level filters.

The system calculates a Regime Coefficient (RC) before each run to scale position sizing. This prevents the system from "fighting the tape" when macro conditions are unfavorable.

* **Gold/Silver Logic**: If GDX is trading below its 50-day Moving Average, all Monetary Metal entries are capped at 50% of the calculated risk budget. If DXY is also in an uptrend (Price > 20d MA), the risk is further reduced by 50% (cumulative 25% of original budget).
* **Copper/Industrial Logic**: Copper trades are governed primarily by COPX trend. If COPX is above its 200-day Moving Average, the regime is considered "Industrial Bullish." The DXY trend is ignored for Copper unless the dollar index is at a 52-week high.
* **Relative Strength Confirmation**: The system compares GDXJ (Juniors) vs GDX (Seniors). If GDXJ/GDX > 1.0 (on a 14-day lookback), it indicates high risk-appetite in the sector, allowing the bot to prioritize "Explorer" and "Developer" business types.

---

### 3.9 Trade Execution

For each selected candidate:

#### a) Position Sizing

Position size is determined by:

position_size = (total_equity * risk_per_trade) / (ATR(14) * ATR_multiplier)

ATR(14) = average true range over past 14 days

ATR multiplier is typically 2.

---

#### b) Constraint Checks

Before execution, enforce:

* Max exposure per metal (to be parametrized)
* Max exposure per business type (e.g. explorers cap)
* Correlation-based exposure limits
* Risk budget availability

---

#### c) Order Placement

Trades are executed via Alpaca with:

* Entry price
* Stop-loss
* Take-profit

Expiry date data will be stored as metadata and will be checked by the system as part of the trading loop.

---

#### d) Trade Metadata

Each trade records:

**Human-readable thesis**

* Narrative explanation of the trade

**Machine-readable snapshot**

* Feature values
* Score breakdown
* Ranking position
* Expiry date

Trade metadata will be stored in SQLite. Also a smaller, human-readable version of this data will be stored in Google Sheets.

---

## 4. Data Storage

The system maintains the following tables:

* **universe**: eligible tickers and classifications
* **positions**: active trades and metadata
* **trades**: historical trades and outcomes
* **features**: feature snapshots at trade entry
* **cache**: cached research results with time-based invalidation
* **insights**: extracted system-level learnings

This data will be stored in SQLite. Additionally, we will store the following data in Google Sheets

* Current open positions with thesises
* Historical trades with outcomes and learnings
* Global learnings _for the operator_, suggestions to improve the system rather than trading patterns (e.g. "reduce or increase pipeline frequency" or "expand ticker universe", as opposed to "gold correlation with silver is weakening")

The Google Sheet is mirrored across two spreadsheets — one for testing (`GOOGLE_SHEET_ID_TEST`) and one for production (`GOOGLE_SHEET_ID_PROD`) — sharing identical tab structure (`universe`, `holdings`, `closed`, `learnings`). The pipeline selects between them via the `--debug/--no-debug` CLI flag, which is plumbed explicitly into the `SheetsClient` factory (no env-var coupling inside components). Authentication uses a Google service account; the JSON key path is read from `GOOGLE_CREDS_PATH` and the sheets must be shared with the service account's `client_email`. The first iteration implements typed CRUD over `universe` (ticker, description) and `holdings` (date, ticker, entry/stop/take prices as `Decimal`, expiry days, thesis); `closed` and `learnings` are deferred.

---

## 5. Caching Strategy

Features are cached based on update frequency:

* Slow-moving (fundamentals): weekly/monthly
* Medium (technicals): daily
* Fast (sentiment, price): refreshed every run

---

## 6. Learning Systems

### 6.1 Structured Trade Data

Each trade is stored with:

* Input features
* Decision outcome
* Performance metrics

Used for:

* Feature evaluation
* Scoring refinement
* Backtesting (partial)

---

### 6.2 Meta-Learning (System Insights)

Periodically, the system analyzes historical trades to extract insights such as:

* Signal effectiveness
* Strategy weaknesses
* Overtrading or undertrading patterns

These insights are stored as structured recommendations and may influence:

* Filtering rules
* Scoring weights
* Execution frequency

---

### 6.3 Shadow Tracking & Counterfactual Analysis

To validate the efficacy of the Scoring & Ranking engine (3.6) and the Risk Budgeting constraints (3.3), the system performs "Shadow Tracking" on the top 3 rejected candidates from each execution run. These "Shadow Trades" are recorded in the trades table with a shadow flag, capturing their entry features and theoretical entry price. On a 14-day and 28-day lag, the system evaluates the performance of these rejected candidates against the active portfolio. This counterfactual data allows the operator to identify if the system is "filtering out alpha" (rejecting winners) or if the qualitative deep research stage (3.7) is successfully avoiding "value traps" that the quantitative filters missed.

---


---

## 7. Backtesting & Validation Strategy
Full-system backtesting is not feasible for this architecture. The system contains components that cannot be historically replicated without introducing lookahead bias or false assumptions:

* LLM-generated summaries and sentiment signals are not reproducible for past dates
* Scoring weights evolve via the learning loop and were not available at historical decision points
* Regime filter parameters are implicitly informed by observed historical regimes

Instead, the system adopts a layered validation approach: offline signal testing for deterministic components, and online paper trading as the primary validation environment for the full pipeline.


### 7.1 Offline: Stage 1 Filter Backtesting
The quantitative filters in Stage 1 (3.5) operate purely on price and volume data and can be historically simulated without bias.

**Method:**

* For each trading day in a 2-year lookback window, apply Stage 1 filters to the eligible universe
* Record which tickers would have passed
* Measure their forward returns at 14-day and 28-day horizons
* Compare against GDX as benchmark

**Success criteria:**

* Median forward return of filter-passing tickers > GDX median return over same horizon
* Hit rate (% of filter-passing tickers outperforming GDX) > 55%

This is a one-time analysis, re-run only if Stage 1 filter logic changes materially.

### 7.2 Offline: Individual Signal Evaluation
Each scoring signal (momentum, volume spike, breakout, relative strength) is evaluated independently:

* Apply signal to historical universe
* Measure information coefficient (IC): correlation between signal value and forward 14d return
* Discard signals with IC near zero or negative across multiple market regimes

This prevents weak signals from polluting the scoring function.

### 7.3 Online: Paper Trading as Primary Validation
The paper trading environment is the authoritative testing ground for the full pipeline. The first 3 months of operation are treated as a calibration phase, not a performance phase. No conclusions about system quality should be drawn before this period completes.

Metrics tracked during calibration:

* Win rate and average return vs GDX benchmark
* Stage 3 deep research lift: do deep-researched candidates outperform Stage 2 rejects?
* Risk budget utilization: is the system too conservative or too aggressive?
* Pipeline health: data freshness, fill rates, error rates

### 7.4 Online: Shadow Trade Validation
As described in section 6.3, the top 3 rejected candidates from each run are tracked as shadow trades.
This serves as a continuous, bias-free backtest of two specific questions:

* Filter alpha: are the Stage 1/2 filters removing candidates that would have won?
* Deep research value: is Stage 3 successfully identifying traps that quant scoring missed?

Shadow trade outcomes are evaluated at 14-day and 28-day lags and stored alongside active trade outcomes for direct comparison.

### 7.5 Position Sizing Stress Test
Before live paper trading begins, ATR-based position sizing is stress-tested against historical volatile periods (e.g. March 2020, Q4 2022) to verify:

* No single position would have exceeded max risk threshold
* Position sizes remain executable given typical junior miner liquidity

This is a one-time pre-launch check, implemented as a standalone script.

---

## 8. Observability

All decisions are logged with:

* Input features
* Scores and rankings
* Accepted/rejected trade rationale

A local Metabase instance provides visibility into:

* Portfolio state
* Trade history
* Feature distributions
* System performance

---

## 9. Execution Environment

* Runs locally on a scheduled job
* Uses PydanticAI
* Integrates with:
  * Alpaca (execution + market data)
  * Finnhub / TwelveData (data sources)
  * External sentiment sources

---

## 10. Future Improvements

* Partial backtesting using historical price data
* Dynamic weight optimization
* Improved correlation clustering
* Enhanced regime detection models

---

## 11. Summary

This system is designed to:

* Filter aggressively
* Allocate capital conservatively
* Act only when high-confidence opportunities arise

The emphasis is on:

* Consistency
* Risk control
* Iterative improvement

Not prediction or overfitting.
