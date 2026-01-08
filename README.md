# 🤖 Algorithmic Crypto Trading Research Platform

**Status**: Phase 1 Complete - Production Ready  
**Last Updated**: January 8, 2026

A professional algorithmic trading research platform with **alpha-score architecture** and **portfolio management** capabilities.

---

## 📚 Documentation Guide

- **[PROJECT_STATE.md](PROJECT_STATE.md)** ⭐ **START HERE** - Complete project overview, current state, and developer handoff
- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step tutorial for first-time setup
- **[plan_now.md](plan_now.md)** - Phase 1 implementation details (completed)
- **[plan_future.md](plan_future.md)** - Phase 2 roadmap (LLM evolution)
- **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** - Detailed Phase 1 completion report

---

## ⚡ Quick Start (5 minutes)

```bash
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py load_strategies

# Run server
python manage.py runserver 9000

# Visit: http://127.0.0.1:9000/
```

**Next Steps**: See [QUICKSTART.md](QUICKSTART.md) for detailed tutorial.

---

## 🎯 What This Platform Does

### **Core Features**
- **Backtest trading strategies** on historical cryptocurrency data
- **Combine multiple strategies** into portfolios
- **Alpha-score system** (industry-standard quantitative approach)
- **14+ evaluation metrics** (Sharpe, Sortino, Calmar, IC, etc.)
- **Web interface** for configuration and results
- **Portfolio optimization** with 4 combination × 4 allocation methods

### **NOT for Live Trading Yet**
This is a research and backtesting tool. Phase 2 will add live trading capabilities.

---

## 🏗️ Architecture

### **Three-Layer Design**

```
┌─────────────────────────────────────────────────┐
│  1. Strategy Layer                              │
│     - Individual strategies generate signals    │
│     - Alpha score: -1 to +1 (conviction)       │
│     - Confidence: 0 to 1 (certainty)           │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  2. Portfolio Layer (Phase 1 ✅)                │
│     - Combines multiple strategy signals        │
│     - 4 combination methods                     │
│     - 4 capital allocation methods              │
└─────────────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────┐
│  3. Execution Layer (Phase 2 - Future)          │
│     - Order management                          │
│     - Risk controls                             │
│     - Live trading                              │
└─────────────────────────────────────────────────┘
```

### **Technology Stack**
- **Django 4.2.9**: Web framework + database ORM
- **Pure Python Engine**: No Django dependencies in core logic
- **Pandas/NumPy**: Data analysis
- **CCXT**: Exchange connectivity
- **SQLite**: Database (PostgreSQL-ready)

---

## 📁 Project Structure

```
alg_trader/
├── core_engine/              # Trading logic (pure Python)
│   ├── strategies/          # 3 built-in strategies
│   ├── portfolio/          # Portfolio management ✨ NEW
│   ├── evaluation/         # Performance metrics ✨ NEW
│   ├── backtest/           # Backtesting engine
│   ├── data/               # Exchange connectivity
│   ├── features/           # Technical indicators
│   └── risk/               # Risk management
├── trading/                # Django web app
│   ├── templates/          # HTML templates
│   ├── management/         # CLI commands
│   └── models.py           # Database models
├── webapp/                 # Django settings
├── PROJECT_STATE.md        # ⭐ Developer handoff doc
├── README.md               # This file
└── requirements.txt        # Dependencies
```

**Full structure**: See [STRUCTURE.md](STRUCTURE.md)

---

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

## 🎨 Key Features (Phase 1 Complete)

### **Alpha-Score Architecture** ✅
- Strategies output **alpha scores** (-1 to +1) instead of binary buy/sell
- Each signal includes **confidence level** (0 to 1)
- **Metadata** for transparency and debugging
- Industry-standard approach used by quantitative hedge funds

### **Portfolio Management** ✅
Combine multiple strategies intelligently:

**4 Signal Combination Methods:**
- **Weighted Average**: Equal or custom weights
- **Confidence Weighted**: Trust confident signals more
- **Rank Average**: Robust to outliers
- **Best Strategy**: Use most confident

**4 Capital Allocation Methods:**
- **Proportional**: Larger positions for stronger signals
- **Equal Weight**: Same size all positions
- **Top N**: Only trade best N signals
- **Threshold**: Tiered sizing by alpha strength

### **Enhanced Evaluation** ✅
14+ metrics including:
- Sharpe, Sortino, Calmar ratios
- Information Coefficient (predictive power)
- Alpha decay analysis
- Strategy comparison tools

### **Web Interface** ✅
- Portfolio manager page
- Data selection from ingested history
- Arbitrary date range selection
- Results visualization
- Strategy comparison

---

## 💻 Usage Examples

### Web Interface (Recommended)

1. **Start server**: `python manage.py runserver 9000`
2. **Ingest data**: Go to Data Management → Ingest Data
3. **Test strategy**: Strategies → Select one → Run Backtest
4. **Test portfolio**: Portfolio → Select strategies → Configure → Run

### Command Line

**Ingest with specific date range:**
```bash
python manage.py ingest_market_data \
    --symbols "BTCUSDT,ETHUSDT" \
    --timeframe 1h \
    --start-date "2025-01-01" \
    --end-date "2025-12-31" \
    --provider mock  # or ccxt
```

**Run single strategy backtest:**
```bash
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTCUSDT" \
    --start-date "2025-12-01" \
    --end-date "2025-12-31"
```

---

## 📊 Built-in Strategies

### 1. Bollinger Mean Reversion
- **Timeframe**: 1h
- **Logic**: Buy oversold, sell overbought (mean reversion)
- **Indicators**: Bollinger Bands, RSI, Volume, ATR
- **Alpha**: Setup quality score
- **Confidence**: Oversold strength + volume

### 2. MACD RSI Confluence
- **Timeframe**: 4h
- **Logic**: Momentum confirmation with MACD + RSI

### 3. Momentum Rank
- **Timeframe**: 1d
- **Logic**: Multi-timeframe momentum alignment
- **Indicators**: Multi-period momentum, Volume Z-score, ATR
- **Alpha**: Momentum score
- **Confidence**: Timeframe agreement

---

## 🛠️ Development

### Adding a New Strategy

See [PROJECT_STATE.md](PROJECT_STATE.md) for detailed workflow.

**Quick steps:**
1. Create file in `core_engine/strategies/your_strategy.py`
2. Inherit from `BaseStrategy`
3. Implement `generate_alpha_signal()` method
4. Add to database: `python manage.py load_strategies`

### Database Changes

```bash
# After modifying models.py
python manage.py makemigrations
python manage.py migrate
```

### Testing

```bash
# Test with mock data (no network required)
python manage.py ingest_market_data \
    --symbols "BTCUSDT" \
    --timeframe 1h \
    --start-date 30 \
    --provider mock

# Run backtest
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTCUSDT" \
    --start-date "2025-12-01" \
    --end-date "2025-12-31"
```

---

## 🔮 Future Roadmap (Phase 2)

See [plan_future.md](plan_future.md) for complete details.

**Next Steps:**
- LLM integration for strategy generation
- Code validation and safety
- Strategy version control (Git)
- Overfitting detection
- Regime analysis
- A/B testing framework
- Auto-rollback mechanisms

**Goal**: Self-evolving trading system where AI generates, tests, and deploys new strategies.

---

## 📚 Documentation

- **[PROJECT_STATE.md](PROJECT_STATE.md)** - Complete system overview and handoff
- **[QUICKSTART.md](QUICKSTART.md)** - Step-by-step tutorial
- **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** - Phase 1 detailed report
- **[plan_now.md](plan_now.md)** - Phase 1 implementation plan
- **[plan_future.md](plan_future.md)** - Phase 2 roadmap
- **[STRUCTURE.md](STRUCTURE.md)** - Detailed file structure

---

## ⚠️ Disclaimer

This is a research and educational tool. **NOT financial advice**. 

- Backtesting does not guarantee future results
- Past performance is not indicative of future returns
- Cryptocurrencies are highly volatile and risky
- Only trade with money you can afford to lose
- Paper trade extensively before considering real trading
- Understand the strategies before using them

---

## 📄 License

See [LICENSE](LICENSE) file for details.

---

**Ready to start?** Read [PROJECT_STATE.md](PROJECT_STATE.md) for complete context, then follow [QUICKSTART.md](QUICKSTART.md).
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