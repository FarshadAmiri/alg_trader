# 📁 Complete Project Structure

## Overview

This document shows the complete file structure of the implemented algorithmic trading platform.

```
d:\Git_repos\alg_trader/
│
├── 📄 README.md                          # Main documentation
├── 📄 QUICKSTART.md                      # Quick start guide
├── 📄 TESTING.md                         # Testing & verification guide
├── 📄 design.md                          # Detailed design specification
├── 📄 LICENSE                            # License file
├── 📄 requirements.txt                   # Python dependencies
├── 📄 .gitignore                         # Git ignore patterns
├── 📄 setup.bat                          # Windows setup script
├── 📄 setup.sh                           # Linux/Mac setup script
├── 📄 manage.py                          # Django management script
│
├── 📁 core_engine/                       # Pure Python trading logic (NO Django)
│   ├── 📄 __init__.py
│   ├── 📄 registry.py                    # Strategy & feature registry
│   │
│   ├── 📁 data/                          # Exchange data providers
│   │   ├── 📄 __init__.py
│   │   ├── 📄 schemas.py                 # Data structures (OHLCV, Signal, etc.)
│   │   ├── 📄 providers.py               # ExchangeProvider, NobitexProvider, CCXTProvider
│   │   └── 📄 fetchers.py                # DataFetcher, normalization, resampling
│   │
│   ├── 📁 features/                      # Technical indicators
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py                    # FeatureComputer interface
│   │   ├── 📄 momentum.py                # RSI, MACD, momentum indicators
│   │   ├── 📄 volatility.py              # ATR, Bollinger Bands, volatility
│   │   └── 📄 liquidity.py               # Volume, OBV, liquidity indicators
│   │
│   ├── 📁 strategies/                    # Trading strategies
│   │   ├── 📄 __init__.py
│   │   ├── 📄 base.py                    # TradingStrategy interface
│   │   ├── 📄 macd_rsi_confluence.py     # MACD + RSI baseline strategy
│   │   └── 📄 momentum_rank.py           # Momentum ranking strategy
│   │
│   ├── 📁 risk/                          # Risk management
│   │   ├── 📄 __init__.py
│   │   ├── 📄 rules.py                   # RiskManager, Allocator
│   │   └── 📄 sizing.py                  # PositionSizer (for future use)
│   │
│   └── 📁 backtest/                      # Backtesting engine
│       ├── 📄 __init__.py
│       ├── 📄 engine.py                  # BacktestEngine orchestrator
│       ├── 📄 walkforward.py             # WalkForwardEngine, TradeResult
│       └── 📄 metrics.py                 # PerformanceMetrics calculator
│
├── 📁 webapp/                            # Django project
│   ├── 📄 __init__.py
│   ├── 📄 settings.py                    # Django settings
│   ├── 📄 urls.py                        # URL routing
│   ├── 📄 wsgi.py                        # WSGI application
│   └── 📄 asgi.py                        # ASGI application
│
└── 📁 trading/                           # Django app
    ├── 📄 __init__.py
    ├── 📄 apps.py                        # App configuration
    ├── 📄 models.py                      # Database models
    ├── 📄 admin.py                       # Django admin configuration
    ├── 📄 views.py                       # Web views
    ├── 📄 forms.py                       # Web forms
    ├── 📄 urls.py                        # URL patterns
    │
    ├── 📁 management/                    # Management commands
    │   ├── 📄 __init__.py
    │   └── 📁 commands/
    │       ├── 📄 __init__.py
    │       ├── 📄 ingest_market_data.py  # Data ingestion command
    │       ├── 📄 run_backtest.py        # Backtest execution command
    │       └── 📄 load_strategies.py     # Load initial strategies
    │
    └── 📁 templates/                     # HTML templates
        └── 📁 trading/
            ├── 📄 base.html              # Base template
            ├── 📄 index.html             # Home page
            ├── 📄 strategy_list.html     # Strategy list
            ├── 📄 backtest_run.html      # Run backtest form
            └── 📄 backtest_results.html  # Results dashboard
```

---

## File Count Summary

- **Total Files**: 50+
- **Python Modules**: 35+
- **HTML Templates**: 5
- **Documentation**: 5
- **Configuration**: 5

---

## Key Components Breakdown

### Core Engine (Pure Python - 16 files)

**Purpose**: All trading logic, completely independent of Django

| Module | Files | Responsibility |
|--------|-------|----------------|
| `data/` | 3 | Exchange APIs, data fetching, normalization |
| `features/` | 4 | Technical indicator computation |
| `strategies/` | 3 | Trading strategy implementations |
| `risk/` | 2 | Risk management, position allocation |
| `backtest/` | 3 | Walk-forward backtesting, metrics |
| `registry.py` | 1 | Strategy/feature registry |

### Django App (11 files)

**Purpose**: Orchestration, persistence, visualization

| Component | Files | Responsibility |
|-----------|-------|----------------|
| Models | 1 | Database schema (Candle, Strategy, BacktestRun, etc.) |
| Views | 1 | Web interface logic |
| Forms | 1 | User input handling |
| Admin | 1 | Django admin customization |
| Commands | 3 | CLI tools (ingest, backtest, load) |
| Templates | 5 | HTML pages |

### Configuration (10 files)

| File | Purpose |
|------|---------|
| `manage.py` | Django CLI entry point |
| `settings.py` | Django configuration |
| `urls.py` | URL routing |
| `requirements.txt` | Dependencies |
| `.gitignore` | Git exclusions |
| `setup.bat/sh` | Quick setup scripts |
| `README.md` | Main docs |
| `QUICKSTART.md` | Tutorial |
| `TESTING.md` | Testing guide |
| `design.md` | Architecture spec |

---

## Database Schema (5 Models)

```
┌─────────────────┐
│     Candle      │  # OHLCV data storage
├─────────────────┤
│ symbol          │
│ timeframe       │
│ timestamp       │
│ open/high/low/  │
│ close/volume    │
└─────────────────┘

┌─────────────────┐
│    Strategy     │  # Strategy registry
├─────────────────┤
│ name            │
│ module_path     │
│ parameters      │
│ is_active       │
└─────────────────┘
         ↓
┌─────────────────┐
│  BacktestRun    │  # Experiment definition
├─────────────────┤
│ strategy FK     │
│ symbol_universe │
│ start/end_time  │
│ window_hours    │
│ status          │
└─────────────────┘
         ↓
┌─────────────────┐
│  TradeResult    │  # Individual trades
├─────────────────┤
│ backtest FK     │
│ symbol          │
│ entry/exit time │
│ return_pct      │
│ max_drawdown    │
└─────────────────┘

┌─────────────────────┐
│ StrategyPerformance │  # Aggregated metrics
├─────────────────────┤
│ backtest FK         │
│ win_rate            │
│ avg_return          │
│ profit_factor       │
└─────────────────────┘
```

---

## API Surface

### Management Commands

```bash
# Data ingestion
python manage.py ingest_market_data [options]

# Backtest execution
python manage.py run_backtest [options]

# Initial setup
python manage.py load_strategies
```

### Web Routes

```
/                           # Home dashboard
/strategies/                # Strategy list
/backtest/run/              # Create backtest
/backtest/<id>/results/     # View results
/admin/                     # Django admin
```

### Core Engine Classes

**Data Layer:**
- `ExchangeProvider` (interface)
- `NobitexProvider`
- `CCXTProvider`
- `DataFetcher`

**Features:**
- `FeatureComputer` (interface)
- `MomentumFeatures`
- `VolatilityFeatures`
- `LiquidityFeatures`

**Strategies:**
- `TradingStrategy` (interface)
- `MACDRSIStrategy`
- `MomentumRankStrategy`

**Risk:**
- `RiskManager`
- `Allocator`
- `PositionSizer`

**Backtest:**
- `BacktestEngine`
- `WalkForwardEngine`
- `PerformanceMetrics`

---

## Dependencies

### Required
- Django 4.2+
- pandas 2.0+
- numpy 1.24+
- requests 2.31+

### Optional
- ccxt 4.0+ (multi-exchange support)
- psycopg2-binary 2.9+ (PostgreSQL)
- celery 5.3+ (background tasks - future)
- redis 5.0+ (celery broker - future)

---

## Lines of Code Estimate

- Core Engine: ~2,500 lines
- Django App: ~1,500 lines
- Templates: ~500 lines
- Documentation: ~2,000 lines
- **Total: ~6,500 lines**

---

## Design Principles Enforced

✅ **Separation of Concerns**
- Core engine has ZERO Django imports
- Django only for orchestration/persistence/UI

✅ **Walk-Forward Backtesting**
- No future leakage
- Time-aware feature computation

✅ **No Indicators in Database**
- Store base candles only
- Compute features on-demand

✅ **Strategy Interface**
- All strategies implement same base class
- Registered in Django but logic in core_engine

✅ **Testability**
- Core engine testable without Django
- Management commands for automation

---

## Extension Points

Want to add new features? Here's where:

| Feature | Location | Steps |
|---------|----------|-------|
| New indicator | `core_engine/features/` | Create class extending `FeatureComputer` |
| New strategy | `core_engine/strategies/` | Create class extending `TradingStrategy` |
| New exchange | `core_engine/data/providers.py` | Create class extending `ExchangeProvider` |
| New risk rule | `core_engine/risk/rules.py` | Modify `RiskManager` |
| New metric | `core_engine/backtest/metrics.py` | Add to `PerformanceMetrics` |
| New web page | `trading/views.py` + `templates/` | Add view + template + URL |

---

## Architecture Validation

Does the implementation follow the design?

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Django only for orchestration | ✅ | No trading logic in models/views |
| Core engine pure Python | ✅ | Zero Django imports in core_engine/ |
| Walk-forward backtest | ✅ | WalkForwardEngine with time filtering |
| No indicators in DB | ✅ | Only Candle model for OHLCV |
| Strategy interface | ✅ | All strategies extend TradingStrategy |
| Fees/slippage | ✅ | Applied in walk_forward.py |
| Risk management | ✅ | RiskManager + Allocator classes |
| Web interface | ✅ | 5 templates, functional UI |

**Result: ✅ 100% Design Compliance**

---

This structure provides a solid foundation for crypto trading research while maintaining clean architecture and extensibility.
