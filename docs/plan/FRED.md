# FRED Macro Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the FRED integration layer (PR 1 — shipped) into the pipeline across the regime filter, scoring engine, and LLM research stage.

**Architecture:** `FredClient` wraps `fredapi.Fred`, fetching 8 macro series per pipeline run and returning a single typed `MacroSnapshot(BaseModel)`. Downstream consumers receive `MacroSnapshot` as an explicit argument — no global state, no env coupling inside components.

**FRED series tracked:**

| Series ID | Description | Frequency |
|-----------|-------------|-----------|
| `DFII10` | 10-Year TIPS Real Yield | Daily |
| `T10YIE` | 10-Year Breakeven Inflation Rate | Daily |
| `DTWEXBGS` | Nominal Broad USD Index | Daily |
| `VIXCLS` | CBOE VIX | Daily |
| `FEDFUNDS` | Effective Federal Funds Rate | Monthly |
| `INDPRO` | Industrial Production Index | Monthly |
| `CPIAUCSL` | CPI All Urban Consumers | Monthly |
| `WPU10` | PPI: Metals & Metal Products | Monthly |

---

## PR 2: Pipeline Wiring

**Status: Blocked — implement once E6 (Stage 2 scoring), E7 (Stage 3 research agent), and E8 (regime filter) exist. This section is a wiring guide for the engineers building those stages, not a standalone workstream to execute now.**

Read `docs/project/ARCHITECTURE.md` sections 3.5–3.8 before starting.

### File Map

| Action | Path | What changes |
|--------|------|-------------|
| Modify | `src/pipelines/trade.py` | Call `make_fred_client`, fetch `MacroSnapshot` early in pipeline run |
| Modify | `src/components/regime/` *(E8)* | Accept `MacroSnapshot`; add three FRED-based regime gates |
| Modify | `src/components/score/` *(E6)* | Accept `MacroSnapshot`; add `real_yield_delta`, `breakeven_delta`, `metals_ppi_delta` score components |
| Modify | `src/components/agents/research/` *(E7)* | Inject `snapshot.to_text()` into the research agent system prompt |
| Modify | `tests/` for each above | Update or add tests for each new integration point |

---

### Task 1: Fetch `MacroSnapshot` in the pipeline entrypoint

**Files:**
- Modify: `src/pipelines/trade.py`

The `run` command already instantiates `settings`. Add the FRED client call immediately after and before any pipeline stage:

- [ ] **Step 1.1: Add the import and client call**

In `src/pipelines/trade.py`, add the import alongside the existing `make_sheets_client` import:

```python
from src.integrations.fred import make_fred_client
```

Inside the `run` command, after `settings = get_settings()`:

```python
fred_client = make_fred_client(settings)
macro_snapshot = fred_client.get_macro_snapshot()
console.print(f"  [dim]macro  :[/dim] FRED snapshot fetched ({macro_snapshot.fetched_at.strftime('%Y-%m-%d')})")
```

Pass `macro_snapshot` as an explicit argument to every stage function that consumes it (regime filter, scoring, research agent). Do not store it as a global or inject it via settings.

- [ ] **Step 1.2: Run the test suite**

```bash
uv run pytest -q
```

Expected: all tests pass. (The FRED call is mocked in unit tests; confirm no integration test tries to hit the network without the `integration` marker.)

- [ ] **Step 1.3: Commit**

```bash
git add src/pipelines/trade.py
git commit -m "feat(fred): fetch MacroSnapshot in pipeline entrypoint"
```

---

### Task 2: Regime Filter integration (E8)

**Files:**
- Modify: `src/components/regime/` (whichever file contains the regime coefficient function)
- Modify: the corresponding test file

The architecture (section 3.8) defines three regime gates for monetary metals plus one for copper. FRED contributes three additional gates that sit alongside the existing GDX/COPX/GDXJ logic.

- [ ] **Step 2.1: Write the failing tests for the three new FRED gates**

In the regime filter test file (e.g., `tests/components/regime_test.py`), add:

```python
from src.schemas.fred import MacroSnapshot, SeriesSnapshot
from datetime import date, datetime, UTC

def _snapshot(
    real_yield: float = 1.5,
    real_yield_delta_14d: float | None = -0.1,
    breakeven_delta_14d: float | None = 0.1,
    metals_ppi_delta_30d: float | None = 1.0,
    usd_delta_14d: float = 0.0,
    indpro_delta_30d: float | None = 1.0,
) -> MacroSnapshot:
    """Minimal MacroSnapshot fixture for regime and scoring tests.

    Place in tests/conftest.py or inline in each test module. All parameters
    default to values that represent a mild gold-bullish macro environment.
    """
    def _snap(series_id: str, value: float, d14: float | None = None, d30: float | None = None) -> SeriesSnapshot:
        return SeriesSnapshot(series_id=series_id, latest_value=value, latest_date=date.today(), delta_14d=d14, delta_30d=d30)
    return MacroSnapshot(
        fetched_at=datetime.now(UTC),
        real_yield_10y=_snap("DFII10", real_yield, d14=real_yield_delta_14d),
        breakeven_inflation_10y=_snap("T10YIE", 2.3, d14=breakeven_delta_14d),
        usd_broad_index=_snap("DTWEXBGS", 105.0, d14=usd_delta_14d),
        vix=_snap("VIXCLS", 18.0),
        fed_funds_rate=_snap("FEDFUNDS", 4.5),
        industrial_production=_snap("INDPRO", 103.0, d30=indpro_delta_30d),
        cpi=_snap("CPIAUCSL", 315.0),
        metals_ppi=_snap("WPU10", 220.0, d30=metals_ppi_delta_30d),
    )


def test_high_real_yield_caps_monetary_metal_budget(/* existing regime fn args */) -> None:
    """Real yield > 2.0% caps monetary metals risk budget at 50%."""
    snapshot = _snapshot(real_yield=2.5)
    result = compute_regime_coefficient(snapshot=snapshot, /* other args */)
    assert result.monetary_metal_budget_multiplier <= 0.5


def test_normal_real_yield_does_not_cap_monetary_metal_budget(/* existing regime fn args */) -> None:
    snapshot = _snapshot(real_yield=1.2)
    result = compute_regime_coefficient(snapshot=snapshot, /* other args */)
    assert result.monetary_metal_budget_multiplier == pytest.approx(1.0)


def test_rising_usd_adds_dollar_headwind_flag(/* existing regime fn args */) -> None:
    """USD broad index trending up (positive 14d delta) sets dollar_headwind=True."""
    snapshot = _snapshot(usd_delta_14d=2.5)
    result = compute_regime_coefficient(snapshot=snapshot, /* other args */)
    assert result.dollar_headwind is True


def test_falling_indpro_downgrades_copper_regime(/* existing regime fn args */) -> None:
    """Negative INDPRO 30d delta downgrades copper to Industrial Cautious."""
    snapshot = _snapshot(indpro_delta_30d=-0.8)
    result = compute_regime_coefficient(snapshot=snapshot, /* other args */)
    assert result.copper_regime == "industrial_cautious"
```

- [ ] **Step 2.2: Implement the three gates in the regime filter**

Add to `compute_regime_coefficient` (wherever the existing GDX/COPX/GDXJ logic lives):

```python
# --- FRED gate 1: real yield cap on monetary metals ---
REAL_YIELD_CAP_THRESHOLD = 2.0  # percentage points
if snapshot.real_yield_10y.latest_value > REAL_YIELD_CAP_THRESHOLD:
    monetary_metal_budget_multiplier = min(monetary_metal_budget_multiplier, 0.5)

# --- FRED gate 2: USD broad index trend ---
USD_HEADWIND_DELTA_THRESHOLD = 1.0  # index points over 14 calendar days
dollar_headwind = (
    snapshot.usd_broad_index.delta_14d is not None
    and snapshot.usd_broad_index.delta_14d > USD_HEADWIND_DELTA_THRESHOLD
)

# --- FRED gate 3: industrial production for copper ---
INDPRO_CONTRACTION_THRESHOLD = 0.0
if (
    snapshot.industrial_production.delta_30d is not None
    and snapshot.industrial_production.delta_30d < INDPRO_CONTRACTION_THRESHOLD
):
    copper_regime = "industrial_cautious"
```

Move the three threshold constants (`REAL_YIELD_CAP_THRESHOLD`, `USD_HEADWIND_DELTA_THRESHOLD`, `INDPRO_CONTRACTION_THRESHOLD`) to `src/constants.py` so they are operator-visible.

- [ ] **Step 2.3: Run tests and confirm all pass**

```bash
uv run pytest tests/components/regime_test.py -v
uv run pytest -q
```

- [ ] **Step 2.4: Commit**

```bash
git add src/components/regime/ src/constants.py tests/components/regime_test.py
git commit -m "feat(fred): wire MacroSnapshot into regime filter gates"
```

---

### Task 3: Stage 2 Scoring integration (E6)

**Files:**
- Modify: `src/components/score/` (whichever file contains the scoring function)
- Modify: the corresponding test file

Three FRED-derived components are added as normalized score signals in the monetary metals scoring path.

- [ ] **Step 3.1: Write the failing tests**

In the scoring test file (e.g., `tests/components/score_test.py`):

```python
from src.schemas.fred import MacroSnapshot, SeriesSnapshot
# reuse _snapshot() fixture from Task 2 or import from a conftest


def test_falling_real_yield_increases_score(base_candidate, baseline_snapshot) -> None:
    """Negative real_yield delta_14d should increase the monetary metals score."""
    snapshot_falling = _snapshot(real_yield_delta_14d=-0.5)
    snapshot_rising  = _snapshot(real_yield_delta_14d=+0.5)
    score_falling = compute_score(base_candidate, snapshot=snapshot_falling)
    score_rising  = compute_score(base_candidate, snapshot=snapshot_rising)
    assert score_falling > score_rising


def test_rising_breakeven_increases_score(base_candidate) -> None:
    """Positive breakeven delta_14d should increase the monetary metals score."""
    snap_up   = _snapshot(breakeven_delta_14d=+0.3)
    snap_down = _snapshot(breakeven_delta_14d=-0.3)
    assert compute_score(base_candidate, snapshot=snap_up) > compute_score(base_candidate, snapshot=snap_down)


def test_rising_metals_ppi_increases_producer_score(producer_candidate) -> None:
    """Positive metals_ppi delta_30d increases score for Producer business type."""
    snap_up   = _snapshot(metals_ppi_delta_30d=+3.0)
    snap_down = _snapshot(metals_ppi_delta_30d=-3.0)
    assert compute_score(producer_candidate, snapshot=snap_up) > compute_score(producer_candidate, snapshot=snap_down)


def test_none_deltas_do_not_raise(base_candidate) -> None:
    """None deltas (insufficient FRED history) are treated as neutral (0.0 contribution)."""
    snap = _snapshot(real_yield_delta_14d=None, breakeven_delta_14d=None, metals_ppi_delta_30d=None)
    score = compute_score(base_candidate, snapshot=snap)
    assert isinstance(score, float)
```

- [ ] **Step 3.2: Add the three FRED score components**

In the scoring function, after the existing signal calculations:

```python
# --- FRED macro signals (monetary metals) ---
REAL_YIELD_DELTA_CLIP = 1.0      # pp; changes beyond this are treated as max signal
BREAKEVEN_DELTA_CLIP = 0.5       # pp
METALS_PPI_DELTA_CLIP = 5.0      # index points

def _normalize(value: float | None, clip: float) -> float:
    """Clip to [-clip, clip] and normalize to [-1, 1]. None → 0 (neutral)."""
    if value is None:
        return 0.0
    return max(-1.0, min(1.0, value / clip))

# Falling real yields are bullish for monetary metals: negate the delta
real_yield_signal   = -_normalize(snapshot.real_yield_10y.delta_14d, REAL_YIELD_DELTA_CLIP)
breakeven_signal    = _normalize(snapshot.breakeven_inflation_10y.delta_14d, BREAKEVEN_DELTA_CLIP)
# Metals PPI only applied for Producer/Royalty/Developer business types
metals_ppi_signal   = (
    _normalize(snapshot.metals_ppi.delta_30d, METALS_PPI_DELTA_CLIP)
    if candidate.business_type in {"Producer", "Royalty", "Developer"}
    else 0.0
)

fred_score = (
    WEIGHT_REAL_YIELD   * real_yield_signal
    + WEIGHT_BREAKEVEN  * breakeven_signal
    + WEIGHT_METALS_PPI * metals_ppi_signal
)
```

Add the weight constants to `src/constants.py`:

```python
WEIGHT_REAL_YIELD = 0.15
WEIGHT_BREAKEVEN  = 0.10
WEIGHT_METALS_PPI = 0.05
```

Move `_normalize` to a shared scoring utilities module if one exists; otherwise define it at the top of the scoring file.

- [ ] **Step 3.3: Run tests**

```bash
uv run pytest tests/components/score_test.py -v
uv run pytest -q
```

- [ ] **Step 3.4: Commit**

```bash
git add src/components/score/ src/constants.py tests/components/score_test.py
git commit -m "feat(fred): add real_yield, breakeven, and metals_ppi scoring signals"
```

---

### Task 4: Stage 3 LLM research agent context injection (E7)

**Files:**
- Modify: `src/components/agents/research/` (whichever file constructs the research agent system prompt)
- Modify: the corresponding test file

- [ ] **Step 4.1: Write the failing test**

In the research agent test file (e.g., `tests/components/agents/research_test.py`):

```python
def test_system_prompt_includes_macro_snapshot(research_agent_deps_fixture) -> None:
    """The research agent system prompt must contain the macro snapshot text block."""
    snapshot = _snapshot()
    # Call the system prompt builder (or the agent's dynamic system prompt function)
    prompt_text = build_research_system_prompt(snapshot=snapshot, /* other args */)
    assert "Macro snapshot" in prompt_text
    assert "Real 10Y yield" in prompt_text


def test_system_prompt_macro_block_reflects_snapshot_values(research_agent_deps_fixture) -> None:
    snapshot = _snapshot(real_yield=3.14)
    prompt_text = build_research_system_prompt(snapshot=snapshot, /* other args */)
    assert "3.14" in prompt_text
```

- [ ] **Step 4.2: Inject `snapshot.to_text()` into the system prompt**

In the research agent module, wherever the system prompt string or dynamic system prompt function is defined:

```python
@agent.system_prompt(dynamic=True)
def research_system_prompt(ctx: RunContext[Deps]) -> str:
    macro_block = ctx.deps.macro_snapshot.to_text()
    return (
        "You are a precious metals equity research analyst.\n\n"
        f"{macro_block}\n\n"
        "Use the macro context above when forming your thesis. "
        "Highlight how the current rate, dollar, and inflation environment affects the candidate."
        # ... rest of existing system prompt ...
    )
```

`Deps` must include `macro_snapshot: MacroSnapshot`. Update the `Deps` dataclass accordingly.

- [ ] **Step 4.3: Run tests**

```bash
uv run pytest tests/components/agents/ -v
uv run pytest -q
```

- [ ] **Step 4.4: Commit**

```bash
git add src/components/agents/research/ tests/components/agents/
git commit -m "feat(fred): inject MacroSnapshot.to_text() into research agent system prompt"
```
