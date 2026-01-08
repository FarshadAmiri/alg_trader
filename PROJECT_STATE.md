# Project State & Developer Handoff Document

**Last Updated**: January 8, 2026  
**Project**: Algorithmic Trading Research Platform  
**Status**: Phase 1 Complete - Production Ready

---

## 🎯 What This Project Does

An **algorithmic trading backtesting platform** for cryptocurrency markets that:
- Tests trading strategies on historical data
- Combines multiple strategies into portfolios
- Uses **alpha-score architecture** (industry-standard approach)
- Provides web interface for configuration and results

**NOT for live trading yet** - research and backtesting only.

---

## 🏗️ Architecture Overview

### **Alpha-Score System** (Phase 1 - COMPLETE)
Instead of simple buy/sell signals, strategies output:
- **Alpha Score**: -1 (strong sell) to +1 (strong buy), 0 = neutral
- **Confidence**: 0 to 1, how certain the strategy is
- **Horizon**: prediction timeframe in days
- **Metadata**: strategy-specific details

### **Three Layers**
1. **Strategy Layer**: Individual strategies generate alpha signals
2. **Portfolio Layer**: Combines multiple strategy signals
3. **Execution Layer**: (Future) converts signals to actual trades

### **Technology Stack**
- **Backend**: Django 4.2.9 (web framework + database)
- **Engine**: Pure Python (no Django dependencies)
- **Database**: SQLite (development), PostgreSQL-ready
- **Data**: CCXT for exchange connectivity
- **Analysis**: Pandas, NumPy for calculations

---

## 📁 Project Structure

```
alg_trader/
├── core_engine/              # Trading logic (pure Python, no Django)
│   ├── strategies/          # Trading strategies
│   │   ├── base.py         # Base classes, StrategySignal dataclass
│   │   ├── bollinger_mean_reversion.py
│   │   ├── macd_rsi_confluence.py
│   │   └── momentum_rank.py
│   ├── portfolio/          # Portfolio management (NEW in Phase 1)
│   │   ├── manager.py      # PortfolioManager orchestrator
│   │   ├── combiners.py    # Signal combination methods
│   │   └── allocators.py   # Capital allocation methods
│   ├── evaluation/         # Performance metrics (NEW in Phase 1)
│   │   ├── strategy_metrics.py  # 14+ evaluation metrics
│   │   └── portfolio_metrics.py # Portfolio comparison
│   ├── backtest/           # Backtesting engine
│   │   ├── engine.py       # Main backtest runner
│   │   ├── metrics.py      # Performance calculation
│   │   └── walkforward.py  # Walk-forward validation
│   ├── data/               # Exchange connectivity
│   │   ├── providers.py    # Binance, CCXT, Mock providers
│   │   └── fetchers.py     # Data fetching logic
│   ├── features/           # Technical indicators
│   │   ├── momentum.py     # MACD, RSI, momentum
│   │   ├── volatility.py   # ATR, Bollinger Bands
│   │   └── liquidity.py    # Volume metrics
│   └── risk/               # Risk management
│       ├── sizing.py       # Position sizing
│       └── rules.py        # Risk rules
├── trading/                # Django app
│   ├── models.py          # Database models
│   ├── views.py           # Web interface views
│   ├── forms.py           # Web forms
│   ├── urls.py            # URL routing
│   ├── templates/         # HTML templates
│   │   └── trading/
│   │       ├── index.html
│   │       ├── backtest_run.html
│   │       ├── backtest_results.html
│   │       ├── portfolio_manager.html      # NEW
│   │       └── portfolio_backtest_results.html  # NEW
│   └── management/commands/  # CLI commands
│       ├── ingest_market_data.py
│       ├── run_backtest.py
│       └── load_strategies.py
├── webapp/                # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── requirements.txt       # Python dependencies
├── manage.py             # Django management script
└── README.md             # Main documentation
```

---

## 🚀 Quick Start for New Developer

### 1. Environment Setup (5 min)

```bash
# Clone or sync repository
cd d:\Git_repos\alg_trader

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Load strategies into database
python manage.py load_strategies
```

### 2. Start Development Server (1 min)

```bash
python manage.py runserver 9000
```

Visit: http://127.0.0.1:9000/

### 3. Load Sample Data (10 min)

**Option A: Via Web Interface**
1. Go to: http://127.0.0.1:9000/ingest-data/
2. Select symbols (BTC/USDT, ETH/USDT)
3. Choose timeframe (1h recommended)
4. Select "Specific Date Range" or "Last N Days"
5. Click "Ingest Data"

**Option B: Via Command Line**
```bash
python manage.py ingest_market_data \
    --symbols "BTCUSDT,ETHUSDT" \
    --timeframe 1h \
    --start-date 30 \
    --provider mock
```

### 4. Test a Strategy (5 min)

**Via Web**: 
- Go to Strategies → Select one → Run Backtest

**Via CLI**:
```bash
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTCUSDT" \
    --start-date "2025-12-01" \
    --end-date "2025-12-31"
```

### 5. Test Portfolio (2 min)

- Go to: http://127.0.0.1:9000/portfolio/
- Select multiple strategies
- Choose combination method (e.g., "Confidence Weighted")
- Choose allocation method (e.g., "Proportional")
- Select data from dropdown (auto-fills dates/symbols)
- Run backtest

---

## 🎨 Key Features Implemented

### **Phase 1 Complete** ✅

1. **Alpha-Score Architecture**
   - `StrategySignal` dataclass with alpha/confidence
   - All 3 strategies refactored to new interface
   - Backward compatible with old signals

2. **Portfolio Management**
   - Combine multiple strategies
   - 4 signal combination methods:
     - Weighted Average
     - Confidence Weighted
     - Rank Average
     - Best Strategy
   - 4 capital allocation methods:
     - Proportional (to alpha)
     - Equal Weight
     - Top N positions
     - Threshold-based

3. **Enhanced Evaluation**
   - 14+ metrics: Sharpe, Sortino, Calmar, IC, etc.
   - Strategy comparison tools
   - Portfolio vs individual performance

4. **Web Interface Updates**
   - Portfolio Manager page
   - Data selection dropdown (shows ingested data)
   - Arbitrary date range selection for data ingest
   - Enhanced results visualization

5. **Database Models**
   - `StrategySignalRecord`: Store alpha signals
   - `PortfolioAllocation`: Track decisions
   - `StrategyEvaluation`: Performance metrics

---

## 🔧 Recent Changes & Fixes

### Latest Session (Jan 8, 2026)

1. **Template Syntax Error** ✅ Fixed
   - Issue: Used non-existent `replace` filter
   - Fix: Changed to if/elif statements for method names

2. **Missing Function** ✅ Fixed
   - Issue: `load_features_for_backtest` not in services.py
   - Fix: Extracted feature loading into reusable function

3. **Data Selection Enhancement** ✅ Added
   - Portfolio page now shows available ingested data
   - Dropdown auto-fills symbol and date range
   - Warns about timeframe compatibility

4. **Arbitrary Date Range** ✅ Added
   - Ingest form now supports specific date ranges
   - Radio toggle between "Last N Days" and "Specific Range"
   - JavaScript handles form visibility

---

## 📊 Current Strategies

### 1. Bollinger Mean Reversion
- **Logic**: Buy oversold, sell overbought (mean reversion)
- **Indicators**: Bollinger Bands, RSI, Volume, ATR
- **Timeframe**: 1h
- **Alpha**: From setup quality (0-1)
- **Confidence**: Oversold strength + volume confirmation

### 2. MACD RSI Confluence
- **Logic**: Momentum confirmation with momentum + oscillator
- **Indicators**: MACD, RSI, Volume, ATR
- **Timeframe**: 4h
- **Alpha**: From momentum ranking
- **Confidence**: MACD strength + optimal RSI

### 3. Momentum Rank
- **Logic**: Multi-timeframe momentum alignment
- **Indicators**: Multi-period momentum, Volume Z-score, ATR
- **Timeframe**: 1d
- **Alpha**: From momentum score
- **Confidence**: Timeframe agreement

---

## 🗄️ Database Schema

### Core Models

**Candle** - OHLCV market data
- symbol, timeframe, timestamp, open, high, low, close, volume

**Strategy** - Strategy definitions
- name, module_path, parameters (JSON), is_active

**BacktestRun** - Backtest configuration & status
- strategy, start_time, end_time, symbol_universe, fee_bps, slippage_bps

**TradeResult** - Individual trade records
- backtest, symbol, entry_time, exit_time, return_pct, max_drawdown

**StrategyPerformance** - Aggregate metrics
- backtest, total_trades, win_rate, avg_return, sharpe_ratio, etc.

### Phase 1 Additions

**StrategySignalRecord** - Alpha signals
- strategy_name, symbol, timestamp, alpha_score, confidence, metadata (JSON)

**PortfolioAllocation** - Capital allocation decisions
- timestamp, combination_method, allocations (JSON), total_capital

**StrategyEvaluation** - Detailed performance
- strategy_name, evaluation_date, sharpe, sortino, calmar, IC, etc.

---

## 🛣️ Future Roadmap (Phase 2)

See [plan_future.md](plan_future.md) for full details.

**Key Next Steps**:
1. LLM Integration for strategy generation
2. Code validation & safety layer
3. Strategy version control (Git)
4. Overfitting detection
5. Regime analysis
6. A/B testing framework
7. Auto-rollback on poor performance

**Goal**: Self-evolving trading system where LLM generates, tests, and deploys new strategies.

---

## 🐛 Known Issues & Limitations

### Current Limitations
1. **No live trading** - backtest only
2. **SQLite database** - good for dev, needs PostgreSQL for production
3. **Single-threaded** - backtests run sequentially
4. **No order book** - assumes perfect liquidity
5. **Basic slippage** - fixed bps, not realistic

### Potential Issues
- Large datasets may slow down (not optimized for >1M candles)
- No API rate limiting protection
- Exchange connectivity depends on network
- Mock provider generates random data (for testing only)

---

## 📚 Documentation Files

### Keep These (Essential)
- **README.md** - Main documentation, architecture, setup
- **QUICKSTART.md** - Step-by-step tutorial
- **plan_now.md** - Phase 1 implementation plan
- **plan_future.md** - Phase 2 roadmap
- **PROJECT_STATE.md** - This file (handoff document)

### Reference (Optional)
- **IMPLEMENTATION_COMPLETE.md** - Detailed Phase 1 completion report
- **STRUCTURE.md** - Detailed file structure
- Strategy READMEs in `core_engine/strategies/`

### Obsolete (Can Delete)
- IMPLEMENTATION_SUMMARY.md (superseded by IMPLEMENTATION_COMPLETE.md)
- UI_CONSISTENCY_UPDATE.md (old update notes)
- POSITION_MANAGEMENT_UPDATE.md (old update notes)
- BOLLINGER_MEAN_REVERSION_STRATEGY.md (moved to strategy folder)
- design.md (incorporated into plans)
- TESTING.md (outdated)

---

## 🔑 Key Concepts to Understand

### 1. Walk-Forward Validation
- Train on window of data
- Test on future period
- Shift window forward
- No future leakage

### 2. Alpha-Score System
- Continuous signal strength vs binary buy/sell
- Allows position sizing proportional to conviction
- Industry standard at quant funds
- Separates prediction from allocation

### 3. Portfolio Construction
- **Signal Combination**: How to merge multiple strategy opinions
- **Capital Allocation**: How to divide capital based on combined signals
- **Constraints**: Max position size, diversification, etc.

### 4. Evaluation Metrics
- **Sharpe Ratio**: Risk-adjusted return
- **Sortino Ratio**: Downside risk-adjusted
- **Calmar Ratio**: Return vs max drawdown
- **Information Coefficient**: Predictive power (alpha vs actual correlation)

---

## 💻 Development Workflow

### Adding a New Strategy

1. Create file in `core_engine/strategies/your_strategy.py`
2. Inherit from `BaseStrategy`
3. Implement required methods:
   - `generate_signals()` (legacy)
   - `generate_alpha_signal()` (Phase 1)
   - `should_close_position()`
4. Add to database:
   ```bash
   python manage.py load_strategies
   ```

### Running Tests

```bash
# Test data fetching
python test_fetch.py

# Test backtest engine
python manage.py run_backtest --strategy "..." --symbols "..."

# View in browser
python manage.py runserver 9000
```

### Database Changes

```bash
# Create migration after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (careful!)
# rm db.sqlite3
# python manage.py migrate
# python manage.py load_strategies
```

---

## 🆘 Troubleshooting

### "No data found for symbol"
- Run data ingestion first
- Check timeframe matches strategy requirement
- Use mock provider if network issues

### "Module not found"
- Activate virtual environment
- Run `pip install -r requirements.txt`

### "Template syntax error"
- Check for typos in template tags
- Ensure context variables are passed from view

### "Migration conflicts"
- Delete db.sqlite3 and migrations (except __init__.py)
- Run `python manage.py makemigrations`
- Run `python manage.py migrate`

---

## 📞 Support & Resources

- **Main Docs**: README.md
- **Quick Tutorial**: QUICKSTART.md
- **Architecture**: See "Architecture Overview" in this file
- **API Docs**: Docstrings in code
- **Django Docs**: https://docs.djangoproject.com/

---

## ✅ Checklist for Next Developer

Before starting work:
- [ ] Read this entire file
- [ ] Review README.md
- [ ] Follow Quick Start steps
- [ ] Successfully run a backtest
- [ ] Test portfolio feature
- [ ] Understand the three layers (Strategy → Portfolio → Execution)
- [ ] Review plan_future.md for Phase 2

**You're ready to continue development!**

---

*This document contains everything needed to understand the current state and continue development. Good luck!*
