# 🚀 Quick Start Guide

## Step-by-Step Tutorial

### 1. Initial Setup (5 minutes)

**Windows:**
```bash
# Run the setup script
setup.bat

# Create admin user
python manage.py createsuperuser
# Enter username, email, password
```

**Linux/Mac:**
```bash
# Make script executable
chmod +x setup.sh

# Run setup
./setup.sh

# Create admin user
python manage.py createsuperuser
```

---

### 2. Ingest Sample Data (10 minutes)

Get 30 days of Bitcoin and Ethereum data from Binance:

```bash
python manage.py ingest_market_data \
    --symbols "BTC/USDT,ETH/USDT" \
    --timeframe 5m \
    --start-date 30 \
    --provider ccxt \
    --exchange binance
```

**Expected output:**
```
Ingesting data for 2 symbols from 2025-12-05 to 2026-01-04
Fetching BTC/USDT...
✓ BTC/USDT: 8640 created, 0 updated
Fetching ETH/USDT...
✓ ETH/USDT: 8640 created, 0 updated
Data ingestion complete
```

---

### 3. Run Your First Backtest (5 minutes)

Test the MACD RSI strategy on the last 2 weeks:

```bash
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTC/USDT,ETH/USDT" \
    --start-date "2025-12-20 00:00" \
    --end-date "2026-01-04 00:00" \
    --window-hours 4 \
    --shift-hours 2
```

**Expected output:**
```
Running backtest: MACD RSI Confluence
Period: 2025-12-20 00:00:00+00:00 to 2026-01-04 00:00:00+00:00
Symbols: BTC/USDT, ETH/USDT
Loading market data...
  BTC/USDT: 4320 candles
  ETH/USDT: 4320 candles
Computing features...
  BTC/USDT: 25 features
  ETH/USDT: 25 features
Initializing strategy...
  Strategy: macd_rsi_confluence
Running backtest...
Saving results...

=== Backtest Results ===
Total Trades: 24
Win Rate: 58.33%
Avg Return: 0.45%
Total Return: 10.80%
Max Drawdown: 2.15%
Profit Factor: 1.85

Backtest #1 completed successfully
```

---

### 4. View Results in Web Interface (2 minutes)

```bash
# Start the development server
python manage.py runserver
```

Open your browser to: **http://127.0.0.1:8000/**

Navigate through:
- **Home**: Dashboard with recent backtests
- **Strategies**: View available strategies
- **Run Backtest**: Create new backtests via web form
- **Results**: Detailed performance metrics and trade-by-trade analysis

---

## Common Commands Cheat Sheet

### Data Management

```bash
# Get 7 days of recent data (quick test)
python manage.py ingest_market_data --symbols "BTC/USDT" --start-date 7 --provider ccxt --exchange binance

# Get specific date range
python manage.py ingest_market_data \
    --symbols "BTC/USDT,ETH/USDT,BNB/USDT" \
    --start-date "2025-12-01" \
    --end-date "2026-01-01" \
    --timeframe 1h \
    --provider ccxt --exchange binance

# Use different exchange
python manage.py ingest_market_data --symbols "BTC/USDT" --start-date 7 --provider ccxt --exchange kraken
```

### Running Backtests

```bash
# Quick test (1 week)
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTC/USDT" \
    --start-date "2025-12-28 00:00" \
    --end-date "2026-01-04 00:00"

# Test different strategy
python manage.py run_backtest \
    --strategy "Momentum Rank" \
    --symbols "BTC/USDT,ETH/USDT,BNB/USDT" \
    --start-date "2025-12-01 00:00" \
    --end-date "2026-01-01 00:00"

# Custom parameters
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTC/USDT" \
    --start-date "2025-12-01 00:00" \
    --end-date "2026-01-01 00:00" \
    --window-hours 8 \
    --shift-hours 4 \
    --fee-bps 20
```

### Django Admin

```bash
# Access admin panel
python manage.py runserver
# Visit: http://127.0.0.1:8000/admin/

# Create superuser
python manage.py createsuperuser

# Django shell (for debugging)
python manage.py shell
```

---

## Testing Different Scenarios

### Scenario 1: Bull Market Testing
Test during known uptrend periods:

```bash
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTC/USDT,ETH/USDT" \
    --start-date "2025-11-01 00:00" \
    --end-date "2025-12-01 00:00"
```

### Scenario 2: High Volatility
Shorter windows during volatile periods:

```bash
python manage.py run_backtest \
    --strategy "Momentum Rank" \
    --symbols "BTC/USDT" \
    --start-date "2025-12-15 00:00" \
    --end-date "2026-01-04 00:00" \
    --window-hours 2 \
    --shift-hours 1
```

### Scenario 3: Multi-Symbol Portfolio
Test across 5+ symbols:

```bash
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTC/USDT,ETH/USDT,BNB/USDT,ADA/USDT,SOL/USDT" \
    --start-date "2025-12-01 00:00" \
    --end-date "2026-01-01 00:00"
```

---

## Troubleshooting

### "No data found for symbol"
→ Run `ingest_market_data` first for that symbol and date range

### "Strategy not found in database"
→ Run `python manage.py load_strategies`

### "Failed to load strategy"
→ Check `module_path` in Django admin matches actual file/class

### Exchange API errors
→ Some exchanges require API keys or have rate limits. Try:
- Use `--provider ccxt --exchange binance` (public data)
- Add delays between requests
- Check exchange status

### Memory issues with large datasets
→ Reduce date range or number of symbols, or increase system RAM

---

## Next Steps

1. **Compare Strategies**: Run both strategies on same data
2. **Optimize Parameters**: Try different RSI/MACD thresholds
3. **Create Custom Strategy**: See README.md for custom strategy guide
4. **Analyze Results**: Use Django admin to export trade data to CSV
5. **Paper Trade**: Monitor live signals (future feature)

---

## Pro Tips

✅ **Start small**: Test with 1 symbol and 1 week before scaling up

✅ **Check data quality**: View candles in Django admin to ensure no gaps

✅ **Fees matter**: 0.10% fee = 0.20% round trip = significant impact on short-term trades

✅ **Multiple timeframes**: Compare 4h vs 8h vs 12h windows

✅ **Symbol selection**: Not all crypto pairs have the same behavior patterns

✅ **Realistic expectations**: 55%+ win rate with 2:1 reward/risk is excellent

---

Happy backtesting! 🚀📈
