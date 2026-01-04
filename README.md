# 🤖 Algorithmic Crypto Trading Research Platform

A systematic crypto trading research platform for evaluating short-term (4-hour) trading opportunities using technical indicators and rule-based strategies.

## 📋 Overview

This platform enables:
- **Data ingestion** from crypto exchanges (Nobitex, CCXT-compatible exchanges)
- **Feature engineering** with technical indicators (MACD, RSI, ATR, volume metrics)
- **Strategy evaluation** using walk-forward backtesting
- **Performance analysis** with comprehensive metrics
- **Web interface** for managing strategies and viewing results

**Important**: This is a research/evaluation tool. Paper trade extensively before considering real trading.

---

## 🏗️ Architecture

The system follows strict separation of concerns:

```
┌─────────────────────────────────────────────────┐
│  Django (webapp + trading app)                  │
│  - Persistence (models)                         │
│  - Orchestration (management commands)          │
│  - Visualization (web UI)                       │
│  - NO trading logic                             │
└─────────────────────────────────────────────────┘
                     ↕
┌─────────────────────────────────────────────────┐
│  core_engine/ (Pure Python - NO Django imports) │
│                                                 │
│  ├── data/         Exchange providers, fetchers │
│  ├── features/     Technical indicators         │
│  ├── strategies/   Trading logic                │
│  ├── risk/         Risk management              │
│  └── backtest/     Walk-forward evaluation      │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
cd d:\Git_repos\alg_trader

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Load initial strategies
python manage.py load_strategies

# Create admin user
python manage.py createsuperuser
```

### 2. Ingest Market Data

```bash
# Example: Fetch 30 days of 5-minute data for BTC and ETH using CCXT (Binance)
python manage.py ingest_market_data \
    --symbols "BTC/USDT,ETH/USDT" \
    --timeframe 5m \
    --start-date 30 \
    --provider ccxt \
    --exchange binance
```

**Options**:
- `--symbols`: Comma-separated list of trading pairs
- `--timeframe`: Candle timeframe (5m, 15m, 1h, 4h, 1d)
- `--start-date`: Days ago or YYYY-MM-DD
- `--end-date`: YYYY-MM-DD (defaults to now)
- `--provider`: `nobitex` or `ccxt`
- `--exchange`: Exchange name for CCXT (binance, kraken, etc.)

### 3. Run Backtest

```bash
# Example: Test MACD RSI strategy on BTC/ETH
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTC/USDT,ETH/USDT" \
    --start-date "2025-12-01 00:00" \
    --end-date "2025-12-15 00:00" \
    --window-hours 4 \
    --shift-hours 2 \
    --fee-bps 10
```

**Options**:
- `--strategy`: Strategy name (from database)
- `--symbols`: Symbols to backtest
- `--start-date`, `--end-date`: Date range
- `--window-hours`: Holding period (default: 4)
- `--shift-hours`: Window shift (default: 2)
- `--fee-bps`: Trading fee in basis points (10 = 0.10%)

### 4. View Results

```bash
# Start development server
python manage.py runserver

# Open browser to http://127.0.0.1:8000/
```

---

## 📊 Built-in Strategies

### 1. MACD RSI Confluence
**Module**: `core_engine.strategies.macd_rsi_confluence:MACDRSIStrategy`

Entry conditions:
- MACD histogram > 0
- RSI between 40-65 (healthy long zone)
- ATR/price < 5% (volatility filter)
- Volume > 80% of average

Ranks symbols by combined momentum/volume score.

### 2. Momentum Rank
**Module**: `core_engine.strategies.momentum_rank:MomentumRankStrategy`

Ranks symbols by multi-timeframe momentum:
- Short/medium/long-term price momentum
- MACD confirmation
- Volume z-score filter
- Volatility cap

---

## 📝 Creating Custom Strategies

1. Create a new file in `core_engine/strategies/`:

```python
from .base import TradingStrategy
import pandas as pd

class MyStrategy(TradingStrategy):
    name = "my_strategy"
    
    def __init__(self, parameters=None):
        super().__init__(parameters)
    
    def select_symbols(self, features_by_symbol, current_time):
        # Your selection logic
        candidates = []
        for symbol, features in features_by_symbol.items():
            latest = self.get_latest_features(features, current_time)
            if latest is not None and self._passes_filters(latest):
                score = self._calculate_score(latest)
                candidates.append((symbol, score))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [s for s, _ in candidates[:3]]
    
    def generate_signal(self, symbol, features, current_time):
        latest = self.get_latest_features(features, current_time)
        if latest is not None and self._my_condition(latest):
            return "LONG"
        return "FLAT"
    
    def _my_condition(self, row):
        # Your entry logic
        return row['rsi'] > 50 and row['macd_histogram'] > 0
```

2. Add to Django:

```bash
# Via Django admin or shell
python manage.py shell

from trading.models import Strategy
Strategy.objects.create(
    name="My Strategy",
    module_path="core_engine.strategies.my_strategy:MyStrategy",
    description="My custom strategy",
    parameters={},
    is_active=True
)
```

---

## 🔧 Configuration

### Database

**SQLite (default)**: Good for development
```python
# webapp/settings.py (already configured)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**PostgreSQL (recommended for production)**:
```python
# Install: pip install psycopg2-binary

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'alg_trader',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Exchange API Keys

For private data or trading (future):
```python
# In your data provider initialization
from core_engine.data.providers import CCXTProvider

provider = CCXTProvider(
    exchange_name='binance',
    api_key='your_api_key',
    api_secret='your_api_secret'
)
```

---

## 📈 Performance Metrics

The system calculates:

- **Total Trades**: Number of evaluated windows
- **Win Rate**: % of profitable trades
- **Average Return**: Mean return per trade (after fees)
- **Total Return**: Sum of returns (no compounding in v1)
- **Max Drawdown**: Maximum peak-to-trough decline
- **Profit Factor**: Gross profit / Gross loss
- **Sharpe Ratio**: Risk-adjusted return

---

## ⚠️ Important Limitations (v1)

1. **No capital compounding**: Each window is independent
2. **LONG only**: No short positions
3. **No live trading**: Research/backtesting only
4. **Simplified execution**: Assumes market orders at close prices
5. **No slippage modeling** (can be added via `--slippage-bps`)

---

## 🛠️ Development

### Project Structure

```
alg_trader/
├── core_engine/              # Pure Python trading logic
│   ├── data/                 # Exchange providers & fetchers
│   ├── features/             # Technical indicators
│   ├── strategies/           # Trading strategies
│   ├── risk/                 # Risk management
│   ├── backtest/             # Walk-forward engine
│   └── registry.py           # Strategy/feature registry
│
├── webapp/                   # Django project
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── trading/                  # Django app
│   ├── models.py             # Database models
│   ├── views.py              # Web views
│   ├── forms.py              # Web forms
│   ├── admin.py              # Admin interface
│   ├── management/commands/  # CLI commands
│   └── templates/            # HTML templates
│
├── manage.py
├── requirements.txt
└── README.md
```

### Running Tests

```bash
# Run Django tests
python manage.py test

# Add your tests in trading/tests.py or core_engine/tests/
```

### Management Commands

```bash
# Ingest data
python manage.py ingest_market_data --help

# Run backtest
python manage.py run_backtest --help

# Load initial strategies
python manage.py load_strategies

# Django shell (for debugging)
python manage.py shell
```

---

## 📚 Next Steps (Future Enhancements)

- [ ] Celery integration for scheduled backtests
- [ ] Paper trading with live market data
- [ ] Capital compounding in backtests
- [ ] Short position support
- [ ] Machine learning strategy integration
- [ ] Multi-exchange arbitrage
- [ ] Real-time dashboard with WebSockets
- [ ] Advanced risk metrics (VaR, CVaR)
- [ ] Portfolio optimization

---

## 📄 License

See [LICENSE](LICENSE) file.

---

## ⚖️ Disclaimer

**This software is for educational and research purposes only.**

- Cryptocurrency trading involves substantial risk of loss
- Past performance does not guarantee future results
- No warranty or guarantee of profitability
- Use at your own risk
- Always paper trade before risking real capital

**The authors are not responsible for any financial losses incurred using this software.**

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Follow the architecture (Django = orchestration, core_engine = logic)
4. Add tests
5. Submit a pull request

---

## 📧 Support

For issues or questions, please open a GitHub issue.