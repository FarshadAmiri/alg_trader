# UI Consistency Update Summary

## Overview
Updated all Django web interface components to align with the simplified strategy auto-configuration design implemented in the command-line interface.

## Design Philosophy
**Before:** Users had to manually specify confusing parameters like `shift_hours=0.1`, `window_hours=4`, and `base_timeframe="5m"`, leading to confusion about what these parameters meant.

**After:** Strategies declare their own metadata (timeframe, evaluation mode, hold times), and the system auto-configures itself. Users only specify:
- Which strategy to run
- Date range
- Symbols
- Trading costs (fees/slippage)
- Optional: Override max hold time

## Files Updated

### 1. Forms (trading/forms.py)
**Changes:**
- ✅ Removed `base_timeframe`, `window_hours`, `shift_hours` from form fields
- ✅ Added `max_hold_override` as optional float field (advanced users only)
- ✅ Updated validation to use strategy's `preferred_timeframe`
- ✅ Enhanced error messages to mention required timeframe

**Key Code:**
```python
fields = ['strategy', 'start_time', 'end_time', 'fee_bps', 'slippage_bps']
max_hold_override = forms.FloatField(required=False, ...)
```

### 2. Views (trading/views.py)
**Changes:**
- ✅ Updated `backtest_run()` to auto-populate model fields from strategy metadata
- ✅ Respects `max_hold_override` if provided by user
- ✅ Updated `execute_backtest()` to use `BacktestEngine.from_strategy()`
- ✅ Loads required timeframe from `strategy.preferred_timeframe`

**Key Code:**
```python
backtest.base_timeframe = strategy_instance.preferred_timeframe
backtest.window_hours = int(backtest.max_hold_override) if backtest.max_hold_override else strategy_instance.max_hold_hours
backtest.shift_hours = strategy_instance.evaluation_interval_hours

engine = BacktestEngine.from_strategy(
    strategy=strategy,
    fee_bps=backtest.fee_bps,
    slippage_bps=backtest.slippage_bps,
    max_hold_override=backtest.max_hold_override
)
```

### 3. Templates

#### backtest_run.html
**Changes:**
- ✅ Removed input fields for `base_timeframe`, `window_hours`, `shift_hours`
- ✅ Added "Strategy Configuration" info box that explains auto-configuration
- ✅ Moved `max_hold_override` to collapsible "Advanced Options" section
- ✅ Updated help texts and labels
- ✅ Updated JavaScript to show strategy info when selected

**UI Improvements:**
- Cleaner, less cluttered form
- Clear indication that strategy auto-configures
- Advanced options hidden by default

#### backtest_results.html
**Changes:**
- ✅ Updated parameter display to show clearer labels:
  - "Timeframe: 5m" instead of "Base Timeframe"
  - "Max Hold: 4h (checks every 2h)" instead of confusing "Window/Shift"
- ✅ Added slippage display when > 0
- ✅ Better fee formatting

#### strategy_list.html
**Changes:**
- ✅ Added info box explaining strategy auto-configuration
- ✅ Listed all 3 strategies with metadata:
  - MACD-RSI: 1h timeframe, periodic every 2h, 4-8h hold
  - Momentum Rank: 15m timeframe, periodic every 1h, 3-6h hold
  - Bollinger Mean Reversion: 5m timeframe, every bar, 30m-4h hold

### 4. Models (trading/models.py)
**Changes:**
- ✅ Added `max_hold_override` field (FloatField, nullable)
- ✅ Updated help texts for `base_timeframe`, `window_hours`, `shift_hours` to clarify they're auto-populated
- ✅ Reorganized field grouping with comments
- ✅ Created migration: `0002_backtestrun_max_hold_override_and_more.py`

**Migration Applied:** ✅ Successfully applied to database

## Testing Checklist

### Command-Line Interface
- [x] `manage.py run_backtest` works without window-hours/shift-hours parameters
- [x] Strategy metadata auto-displays (timeframe, evaluation mode, hold time)
- [x] Backtest finds trades successfully

### Web Interface
To verify everything works:

1. **Strategy List Page** (`/trading/strategies/`)
   - [ ] Visit page and verify all 3 strategies listed with metadata
   - [ ] Check that info box explains auto-configuration

2. **Create Backtest Form** (`/trading/backtest/run/`)
   - [ ] Verify NO fields for base_timeframe, window_hours, shift_hours
   - [ ] Select a strategy - verify "Strategy Configuration" box appears
   - [ ] Expand "Advanced Options" - verify max_hold_override field exists
   - [ ] Select symbols and dates
   - [ ] Submit form and verify it creates backtest

3. **Backtest Results** (`/trading/backtest/results/<id>/`)
   - [ ] Verify display shows "Timeframe: X" and "Max Hold: Xh"
   - [ ] Check performance metrics display correctly
   - [ ] Verify trades table shows

4. **Database**
   - [x] Migration applied successfully
   - [ ] New backtests have auto-populated base_timeframe/window_hours/shift_hours
   - [ ] max_hold_override stored correctly when provided

## Consistency Achieved

### Before This Update
- ❌ CLI simple, web UI confusing
- ❌ Users had to know what "shift_hours=0.1" means
- ❌ Duplicate timeframe specifications
- ❌ No clear guidance on strategy requirements

### After This Update
- ✅ CLI and web UI both use strategy auto-configuration
- ✅ Users only specify high-level parameters
- ✅ Strategy declares requirements, system adapts
- ✅ Clear documentation of each strategy's metadata
- ✅ Database fields auto-populated but preserved for records

## Documentation Updated
- ✅ This summary document
- ✅ Code comments in forms.py, views.py, models.py
- ✅ Template help texts and info boxes
- ✅ Strategy list descriptions

## Backward Compatibility
- ✅ Existing BacktestRun records preserved (fields not removed, just auto-populated)
- ✅ Migration adds new field without breaking existing data
- ✅ Old backtests can still be viewed with original parameters

## Next Steps (Optional Future Enhancements)
1. **AJAX Strategy Info:** Fetch and display full strategy metadata when strategy selected (timeframe, evaluation mode, typical/max hold, description)
2. **Data Validation Indicator:** Show checkmark/warning if required timeframe data exists for selected symbols
3. **Strategy Comparison:** Allow running same backtest with multiple strategies
4. **Results Visualization:** Add charts for equity curve, drawdown, distribution

## Key Takeaway
The entire project is now consistent with the design philosophy: **strategies are self-contained and declare their own requirements**. The system auto-configures to match, eliminating user confusion and parameter duplication.
