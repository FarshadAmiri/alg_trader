---
# Systematic Crypto Trading Research Platform (4h Horizon)

**Purpose:** A research + evaluation platform that ranks crypto symbols for short-term opportunities (4-hour horizon) using features/indicators and rule-based trading strategies (“agents”), then evaluates them with strict walk-forward backtests.

**Scope stance (v1):** Focus on *correctness, reproducibility, and risk-aware ranking* before any real-money execution.

---

## 0) Guiding principles (non‑negotiable)

1) **Django is for orchestration, persistence, and visualization.**
   - No indicator computation inside Django models/views.
   - No strategy logic inside Django models/views.

2) **Core engine is pure Python.**
   - `core_engine/` must have **NO Django imports**.
   - Strategies/features/backtests are testable without running the web app.

3) **No future leakage in evaluation.**
   - All features at time $t$ may only use data strictly at or before $t$.
   - Backtests are walk-forward by construction.

4) **Indicators are derived, not stored.**
   - Store base candles (OHLCV) only.
   - Compute indicators/features on demand (or cache in-memory / ephemeral cache later).

5) **Risk management is part of every strategy evaluation.**
   - A “good signal” without a risk rule is incomplete.

---

## 1) System overview

The system has four main layers:

1) **Data ingestion**: fetch and store normalized OHLCV for a symbol universe.
2) **Feature engineering (Analyst agents)**: compute numeric features (MACD/RSI/ATR/volume metrics, etc.).
3) **Strategies (Trader agents)**: select symbols and issue signals based on features + explicit risk gates.
4) **Evaluation (Backtesting & reports)**: run walk-forward sliding-window backtests and persist results for comparison.

Target horizon:
- **Window:** 4 hours
- **Shift:** 2 hours (overlapping windows)
- Each evaluation slice is independent in v1 (no compounding).

---

## 2) Tech stack (v1)

- **Python** (core computations)
- **Django + Django REST Framework (optional)** for UI + management commands
- **PostgreSQL** recommended; **SQLite** acceptable for early development
- **Celery + Redis** optional later (for scheduled ingestion/backtests)

Exchange/API choice:
- Start with one exchange/data source (simple), but design with a provider interface.
- Example provider: Nobitex (per your preference) or CCXT-compatible exchanges.

---

## 3) Repository / folder structure

```
project_root/
│
├── core_engine/                  # Pure Python (NO Django imports)
│   ├── data/
│   │   ├── providers.py           # Exchange provider interfaces + implementations
│   │   ├── fetchers.py            # Fetch OHLCV, normalize, return DataFrames
│   │   └── schemas.py             # Typed structures / validation helpers
│   │
│   ├── features/
│   │   ├── base.py                # FeatureComputer interface
│   │   ├── momentum.py            # MACD/RSI/momentum features
│   │   ├── volatility.py          # ATR, Bollinger width, etc.
│   │   └── liquidity.py           # Volume z-scores, spreads (if available)
│   │
│   ├── strategies/
│   │   ├── base.py                # TradingStrategy interface
│   │   ├── macd_rsi_confluence.py # Baseline mandatory strategy
│   │   └── momentum_rank.py       # Alternative baseline
│   │
│   ├── risk/
│   │   ├── rules.py               # Risk gates (ATR/price cap, max positions, etc.)
│   │   └── sizing.py              # Position sizing primitives (v2 if compounding)
│   │
│   ├── backtest/
│   │   ├── engine.py              # Backtest runner
│   │   ├── walkforward.py         # Sliding window logic (4h window, 2h shift)
│   │   └── metrics.py             # Aggregations (win rate, drawdown, etc.)
│   │
│   └── registry.py                # Strategy/feature registries
│
├── webapp/                        # Django project
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── trading/                       # Django app
│   ├── models.py                  # Candles, strategy registry, backtest runs, results
│   ├── admin.py
│   ├── views.py                   # List/run/results pages (no computations)
│   ├── forms.py
│   ├── urls.py
│   ├── management/
│   │   └── commands/
│   │       ├── ingest_market_data.py
│   │       └── run_backtest.py
│   └── templates/
│       └── trading/
│           ├── strategy_list.html
│           ├── backtest_run.html
│           └── results.html
│
└── manage.py
```

---

## 4) Data model (Django side)

### 4.1 Candle storage (base timeframe)

**Rule:** store only base candles (e.g., `5m`). Higher timeframes (1h/4h) are aggregated in memory for features.

```python
class Candle(models.Model):
	symbol = models.CharField(max_length=20)
	timeframe = models.CharField(max_length=5)   # "5m"
	timestamp = models.DateTimeField()
	open = models.FloatField()
	high = models.FloatField()
	low = models.FloatField()
	close = models.FloatField()
	volume = models.FloatField()

	class Meta:
		unique_together = ("symbol", "timeframe", "timestamp")
		indexes = [
			models.Index(fields=["symbol", "timeframe", "timestamp"]),
			models.Index(fields=["timestamp"]),
		]
```

### 4.2 Strategy registry (metadata only)

```python
class Strategy(models.Model):
	name = models.CharField(max_length=100, unique=True)
	module_path = models.CharField(max_length=200)  # e.g. core_engine.strategies.macd_rsi_confluence:Strategy
	description = models.TextField(blank=True)
	parameters = models.JSONField(default=dict, blank=True)  # strategy hyperparameters
	is_active = models.BooleanField(default=True)
```

### 4.3 Backtest runs (experiment definition)

```python
class BacktestRun(models.Model):
	strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
	symbol_universe = models.JSONField()  # list[str]
	start_time = models.DateTimeField()
	end_time = models.DateTimeField()
	base_timeframe = models.CharField(max_length=5, default="5m")
	window_hours = models.IntegerField(default=4)
	shift_hours = models.IntegerField(default=2)
	fee_bps = models.IntegerField(default=10)  # 10 bps = 0.10% per side (configurable)
	slippage_bps = models.IntegerField(default=0)  # optional
	created_at = models.DateTimeField(auto_now_add=True)
```

### 4.4 Trade results (slice-level outcomes)

In v1, each window’s “trade” is evaluated independently.

```python
class TradeResult(models.Model):
	backtest = models.ForeignKey(BacktestRun, on_delete=models.CASCADE)
	symbol = models.CharField(max_length=20)
	entry_time = models.DateTimeField()
	exit_time = models.DateTimeField()
	direction = models.CharField(max_length=10, default="LONG")  # v1: LONG only
	return_pct = models.FloatField()        # after fees/slippage
	max_drawdown = models.FloatField()      # within the holding window (approx.)
	metadata = models.JSONField(default=dict, blank=True)  # optional: ranks, feature snapshots
```

### 4.5 Aggregated performance (optional convenience)

Optionally store rollups for UI speed.

```python
class StrategyPerformance(models.Model):
	backtest = models.OneToOneField(BacktestRun, on_delete=models.CASCADE)
	total_trades = models.IntegerField()
	win_rate = models.FloatField()
	avg_return_pct = models.FloatField()
	profit_factor = models.FloatField(null=True)
	max_drawdown = models.FloatField()
```

---

## 5) Core engine: responsibilities and interfaces (Python-only)

### 5.1 Data providers & fetchers

`core_engine/data/providers.py`
- Provider interface for OHLCV retrieval.
- Implementation per exchange (Nobitex, CCXT, etc.).

`core_engine/data/fetchers.py`
- Fetch OHLCV
- Normalize timestamps/timezones
- Return `pandas.DataFrame` with columns: `timestamp, open, high, low, close, volume`

**Rules:**
- No DB writes
- No Django imports

### 5.2 Feature engineering (“Analyst agents”)

Each feature computer:
- Input: OHLCV DataFrame
- Output: DataFrame of **numeric columns only** aligned on timestamp

```python
class FeatureComputer:
	name: str

	def compute(self, df):
		"""Return a DataFrame with new numeric feature columns."""
		raise NotImplementedError
```

Recommended v1 feature set (minimal but useful):
- **Momentum**: RSI, MACD histogram, MACD histogram slope
- **Trend**: EMA(12)/EMA(26) distance, simple trend slope
- **Volatility**: ATR/price, Bollinger bandwidth
- **Liquidity/volume**: volume z-score, volume trend

Feature “favorability” should be expressed as normalized numeric scores (e.g., z-score or percentile rank within universe).

### 5.3 Strategy (“Trader agent”) interface

Strategies act on features at time $t$ to select symbols for the next holding window.

```python
class TradingStrategy:
	name: str

	def select_symbols(self, features_by_symbol, current_time):
		"""Return symbols to trade at time t (ranked or filtered)."""
		raise NotImplementedError

	def generate_signal(self, symbol, features_df, current_time):
		"""Return "LONG" or "FLAT" (v1)."""
		raise NotImplementedError
```

**Mandatory v1 baseline strategy (rule-based):**
- Gate by volatility: `ATR/price <= threshold`
- Momentum confirmation: MACD histogram slope > 0
- RSI in a “healthy long” band (e.g., 40–65)
- Rank candidates by a combined momentum/volume score

### 5.4 Risk rules (explicit)

Risk in v1 is applied as **eligibility gates** and **portfolio constraints** (since we don’t compound capital yet).

```python
class RiskManager:
	def allow_symbol(self, features_row) -> bool:
		raise NotImplementedError


class Allocator:
	def allocate(self, symbols):
		"""Return weights per symbol (sum to 1.0)."""
		raise NotImplementedError
```

Initial constraints:
- Max positions: **3**
- Weights: **equal weights**
- Skip symbol if:
  - volatility too high (`ATR/price > threshold`)
  - insufficient volume (below minimum)
- Fees/slippage applied in backtest results

---

## 6) Backtesting & evaluation (core of correctness)

### 6.1 Walk-forward sliding-window evaluation

For each evaluation time $t$ in `[start, end]` stepping by `shift_hours`:

1) Build a rolling **lookback** dataset ending at $t$ (enough candles to compute features safely).
2) Compute features **using only data ≤ t**.
3) Ask strategy for candidate symbols/signals at $t$.
4) Evaluate realized return over `[t, t + window_hours]`.
5) Apply fees/slippage.
6) Record `TradeResult` rows.

Overlapping windows are allowed; in v1:
- Trades are evaluated independently
- No portfolio compounding

### 6.2 Metrics to compute

Per strategy and per backtest:
- Win rate
- Average return per trade
- Median return
- Profit factor (optional in v1)
- Max drawdown (per-trade and aggregated)
- Trade count, coverage (how often strategy found signals)

### 6.3 Avoiding common evaluation traps

- Always include realistic **fees** (and optionally slippage).
- Be conservative with signals frequency (fees destroy high-churn systems).
- Keep parameter count low in early versions to avoid overfitting.

---

## 7) Django integration flow

### 7.1 Management commands (primary integration point)

1) `python manage.py ingest_market_data`
   - Fetch candles for selected symbols/time range
   - Normalize and upsert into `Candle`

2) `python manage.py run_backtest`
   - Load candles from DB
   - Run `core_engine.backtest.walkforward`
   - Persist `BacktestRun` + `TradeResult` (+ optional rollups)

**Important:** Django views should only display stored results and launch jobs; they must not compute features.

---

## 8) Web interface (minimal Django templates)

No heavy frontend in v1; basic HTML forms + tables.

Pages:
1) **Strategy list**
   - Name, description, active toggle

2) **Run backtest**
   - Strategy
   - Symbol universe
   - Date range
   - Window hours (default 4)
   - Shift hours (default 2)
   - Fees/slippage

3) **Results dashboard**
   - Summary metrics per strategy
   - Trades table (filter by backtest)
   - Basic comparisons across strategies

---

## 9) Development roadmap (pragmatic)

Phase 1 — Foundation
- Django project + `trading` app
- Candle model + ingestion command
- Core engine skeleton + one data provider

Phase 2 — Features & baseline strategy
- Implement minimal features (RSI/MACD/ATR/volume)
- Implement baseline strategy + risk gates

Phase 3 — Walk-forward backtest
- Sliding window engine
- Persist results + compute metrics

Phase 4 — UI
- Strategy registry UI
- Backtest run form
- Results dashboard

Phase 5 — Optional extensions (only after v1 is correct)
- Celery scheduling for ingestion/backtests
- Paper trading “live simulation” mode
- Multi-exchange providers
- Capital compounding + position sizing

---

## 10) Hard constraints for implementation (give these to the coding agent)

- No indicators/features stored in the database
- No trading logic inside Django models/views
- All strategies implement the same base interface
- Backtests must be walk-forward (no future leakage)
- Django only for UI, persistence, orchestration

---

## 11) Safety note

Crypto markets are high risk. This project is designed for research and paper evaluation first. Real trading should only be considered after extensive paper trading and careful risk controls.

