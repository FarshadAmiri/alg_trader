# 🧪 Testing & Verification Guide

## Verify Installation

### 1. Check Python Environment

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Verify Python version (3.8+)
python --version

# Verify packages installed
pip list | findstr Django  # Windows
# pip list | grep Django  # Linux/Mac
```

Expected: Django 4.2+, pandas 2.0+, numpy 1.24+

---

### 2. Test Django Setup

```bash
# Check for errors
python manage.py check

# Expected output: System check identified no issues (0 silenced).
```

```bash
# Test migrations
python manage.py showmigrations

# Should show [X] marks for all trading app migrations
```

---

### 3. Test Core Engine (No Django Dependencies)

```bash
python manage.py shell
```

```python
# Test data fetcher (mock test - no real API call needed)
from core_engine.data.providers import CCXTProvider
from core_engine.data.fetchers import DataFetcher

# This should import without errors
print("✓ Data module OK")

# Test features
from core_engine.features.momentum import MomentumFeatures
from core_engine.features.volatility import VolatilityFeatures
print("✓ Features module OK")

# Test strategies
from core_engine.strategies.macd_rsi_confluence import MACDRSIStrategy
from core_engine.strategies.momentum_rank import MomentumRankStrategy
print("✓ Strategies module OK")

# Test backtest engine
from core_engine.backtest.engine import BacktestEngine
print("✓ Backtest module OK")

# Exit
exit()
```

Expected: All "✓ OK" messages, no import errors

---

## Test Data Ingestion

### Test 1: Small Dataset (Quick)

```bash
# Get just 1 day of data for 1 symbol
python manage.py ingest_market_data \
    --symbols "BTC/USDT" \
    --timeframe 1h \
    --start-date 1 \
    --provider ccxt \
    --exchange binance
```

**Verify in Django shell:**
```python
python manage.py shell

from trading.models import Candle
count = Candle.objects.filter(symbol='BTC/USDT').count()
print(f"Candles loaded: {count}")
# Expected: ~24 candles (1 day of hourly data)

# Check data quality
latest = Candle.objects.filter(symbol='BTC/USDT').latest('timestamp')
print(f"Latest candle: {latest.timestamp}, Close: ${latest.close:,.2f}")
# Should show recent Bitcoin price

exit()
```

---

### Test 2: Feature Computation

```bash
python manage.py shell
```

```python
import pandas as pd
from trading.models import Candle
from core_engine.features.momentum import MomentumFeatures
from core_engine.features.volatility import VolatilityFeatures

# Load candles
candles = Candle.objects.filter(symbol='BTC/USDT', timeframe='1h').order_by('timestamp')
data = list(candles.values('timestamp', 'open', 'high', 'low', 'close', 'volume'))
df = pd.DataFrame(data)

print(f"Loaded {len(df)} candles")

# Compute features
momentum = MomentumFeatures()
df = momentum.compute(df)

volatility = VolatilityFeatures()
df = volatility.compute(df)

# Check features
print(f"\nFeatures computed: {len(df.columns)}")
print(f"Columns: {list(df.columns)}")

# Show latest values
latest = df.iloc[-1]
print(f"\nLatest RSI: {latest['rsi']:.2f}")
print(f"Latest MACD: {latest['macd_histogram']:.4f}")
print(f"Latest ATR%: {latest['atr_pct']:.2f}%")

exit()
```

Expected: RSI between 0-100, reasonable MACD values, ATR > 0

---

## Test Backtesting

### Test 3: Mini Backtest (Fast)

```bash
# Run 3-day backtest
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTC/USDT" \
    --start-date "2026-01-01 00:00" \
    --end-date "2026-01-04 00:00" \
    --window-hours 4 \
    --shift-hours 2
```

**Expected Output Pattern:**
```
Running backtest: MACD RSI Confluence
Period: 2026-01-01 00:00:00+00:00 to 2026-01-04 00:00:00+00:00
Symbols: BTC/USDT
Loading market data...
  BTC/USDT: XXX candles
Computing features...
  BTC/USDT: 25+ features
Initializing strategy...
Running backtest...
Saving results...

=== Backtest Results ===
Total Trades: X
Win Rate: XX.XX%
Avg Return: X.XX%
...
Backtest #X completed successfully
```

**Verify Results:**
```bash
python manage.py shell
```

```python
from trading.models import BacktestRun, TradeResult, StrategyPerformance

# Check backtest created
latest_backtest = BacktestRun.objects.latest('created_at')
print(f"Backtest #{latest_backtest.id}: {latest_backtest.status}")
# Expected: status = 'completed'

# Check trades
trades = TradeResult.objects.filter(backtest=latest_backtest)
print(f"Trades executed: {trades.count()}")

# Check performance
perf = StrategyPerformance.objects.get(backtest=latest_backtest)
print(f"Win rate: {perf.win_rate:.1f}%")
print(f"Avg return: {perf.avg_return_pct:.2f}%")

exit()
```

---

## Test Web Interface

### Test 4: Web Server

```bash
# Start server
python manage.py runserver
```

**Manual Tests:**

1. **Home Page** - http://127.0.0.1:8000/
   - ✓ Dashboard loads
   - ✓ Shows strategy count
   - ✓ Shows recent backtests

2. **Strategies** - http://127.0.0.1:8000/strategies/
   - ✓ Lists MACD RSI Confluence
   - ✓ Lists Momentum Rank
   - ✓ Both show as Active

3. **Admin** - http://127.0.0.1:8000/admin/
   - ✓ Login works
   - ✓ Can view Candles
   - ✓ Can view Strategies
   - ✓ Can view Backtest Runs

4. **Backtest Form** - http://127.0.0.1:8000/backtest/run/
   - ✓ Form renders
   - ✓ Strategy dropdown populated
   - ✓ All fields present

5. **Results Page** - http://127.0.0.1:8000/backtest/1/results/
   - ✓ Shows metrics (if backtest #1 completed)
   - ✓ Shows trade table
   - ✓ Charts/stats display correctly

---

## Integration Tests

### Test 5: Full Workflow

```bash
# 1. Fresh start
python manage.py flush --no-input
python manage.py migrate
python manage.py load_strategies

# 2. Ingest data
python manage.py ingest_market_data \
    --symbols "BTC/USDT,ETH/USDT" \
    --timeframe 1h \
    --start-date 14 \
    --provider ccxt \
    --exchange binance

# 3. Run backtest
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTC/USDT,ETH/USDT" \
    --start-date "2025-12-25 00:00" \
    --end-date "2026-01-04 00:00" \
    --window-hours 4 \
    --shift-hours 2

# 4. Verify
python manage.py shell
```

```python
from trading.models import Candle, Strategy, BacktestRun, TradeResult

# Data check
btc_count = Candle.objects.filter(symbol='BTC/USDT').count()
eth_count = Candle.objects.filter(symbol='ETH/USDT').count()
print(f"BTC candles: {btc_count}")
print(f"ETH candles: {eth_count}")

# Strategy check
strategies = Strategy.objects.filter(is_active=True).count()
print(f"Active strategies: {strategies}")

# Backtest check
backtests = BacktestRun.objects.filter(status='completed').count()
print(f"Completed backtests: {backtests}")

# Trade check
total_trades = TradeResult.objects.count()
print(f"Total trades: {total_trades}")

# Performance check
latest_bt = BacktestRun.objects.latest('created_at')
perf = latest_bt.strategyperformance
print(f"\nLatest backtest performance:")
print(f"  Win rate: {perf.win_rate:.1f}%")
print(f"  Total return: {perf.total_return_pct:.2f}%")
print(f"  Max DD: {perf.max_drawdown:.2f}%")

exit()
```

**Expected:**
- ✓ Hundreds of candles for each symbol
- ✓ 2 active strategies
- ✓ At least 1 completed backtest
- ✓ Multiple trades recorded
- ✓ Performance metrics calculated

---

## Edge Cases & Error Handling

### Test 6: Error Conditions

```bash
# Test: Missing data
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "INVALID/SYMBOL" \
    --start-date "2026-01-01 00:00" \
    --end-date "2026-01-04 00:00"

# Expected: Graceful error, backtest status = 'failed'
```

```bash
# Test: Invalid date range
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTC/USDT" \
    --start-date "2026-01-10 00:00" \
    --end-date "2026-01-01 00:00"

# Expected: Error about date range
```

```bash
# Test: Nonexistent strategy
python manage.py run_backtest \
    --strategy "Fake Strategy" \
    --symbols "BTC/USDT" \
    --start-date "2026-01-01 00:00" \
    --end-date "2026-01-04 00:00"

# Expected: "Strategy not found in database"
```

---

## Performance Tests

### Test 7: Large Dataset

```bash
# Test with 30 days of 5-minute data
python manage.py ingest_market_data \
    --symbols "BTC/USDT" \
    --timeframe 5m \
    --start-date 30 \
    --provider ccxt \
    --exchange binance

# This should create ~8,640 candles (30 days * 288 candles/day)
```

```bash
# Run backtest on large dataset
python manage.py run_backtest \
    --strategy "MACD RSI Confluence" \
    --symbols "BTC/USDT" \
    --start-date "2025-12-05 00:00" \
    --end-date "2026-01-04 00:00" \
    --window-hours 4 \
    --shift-hours 1
```

**Monitor:**
- Memory usage should stay < 2GB
- Execution time < 5 minutes
- No memory errors

---

## Verification Checklist

### Before Deployment

- [ ] All migrations applied
- [ ] Initial strategies loaded
- [ ] Can ingest data successfully
- [ ] Features compute without errors
- [ ] Backtests run and complete
- [ ] Web interface loads all pages
- [ ] Admin panel accessible
- [ ] Trade results visible
- [ ] Performance metrics calculated
- [ ] No Python errors in console
- [ ] Database queries performant
- [ ] Error handling graceful

### Quality Checks

- [ ] Win rate between 0-100%
- [ ] Returns realistic (not 1000%+)
- [ ] Max drawdown ≥ 0
- [ ] Trade count matches expected windows
- [ ] No future leakage (manually verify signals use only past data)
- [ ] Fees applied correctly (compare gross vs net returns)
- [ ] Timestamps in correct timezone

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Import errors | `pip install -r requirements.txt` |
| "No module named 'trading'" | Run from project root directory |
| Database locked | Close other connections, restart |
| Exchange API timeout | Try different exchange or increase timeout |
| Feature computation slow | Reduce date range or use higher timeframe |
| Empty backtest results | Check data exists for date range |
| Web page 404 | Check `urlpatterns` in urls.py |

---

## Success Criteria

✅ **System is working if:**

1. Data ingestion creates candles in database
2. Features compute with reasonable values
3. Backtests complete with status='completed'
4. Trade results are created
5. Performance metrics calculated
6. Web interface shows all data
7. No critical errors in logs

✅ **System is production-ready if:**

1. All above tests pass
2. Handles 10K+ candles smoothly
3. Multiple symbols backtest successfully
4. Error conditions handled gracefully
5. Web interface responsive
6. Documentation accurate
7. Code follows design principles

---

**When all tests pass, you're ready to start real research! 🎉**
