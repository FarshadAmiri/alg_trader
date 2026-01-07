# Position Management Architecture Update

## Summary

Successfully redesigned the strategy system to support dynamic position management where each strategy defines its own entry AND exit conditions, replacing the previous fixed 4-hour holding period.

## Key Changes

### 1. Base Strategy Class ([base.py](core_engine/strategies/base.py))

Added new abstract method `should_close_position()`:
- **Parameters**: symbol, features, entry_time, current_time, entry_price, current_price
- **Returns**: Boolean indicating whether to close the position
- **Purpose**: Allows each strategy to implement custom exit logic based on technical indicators, P&L targets, time limits, or market conditions

### 2. MACD-RSI Strategy ([macd_rsi_confluence.py](core_engine/strategies/macd_rsi_confluence.py))

**Entry conditions** (unchanged):
- RSI in healthy range (40-65)
- MACD histogram positive
- Volatility filter (ATR < 5%)
- Volume confirmation

**New exit conditions**:
- **Take profit**: +6% gain
- **Stop loss**: -3% loss
- **RSI overbought**: >75 (momentum exhaustion)
- **MACD reversal**: histogram turns negative
- **Max hold time**: 8 hours (safety fallback)

### 3. Momentum Rank Strategy ([momentum_rank.py](core_engine/strategies/momentum_rank.py))

**Entry conditions** (unchanged):
- Positive momentum score (>0.2)
- Controlled volatility (ATR < 6%)
- Volume confirmation

**New exit conditions**:
- **Take profit**: +5% gain (faster exits for momentum)
- **Stop loss**: -2.5% loss (tighter control)
- **Momentum deterioration**: score drops below 0.1
- **Volume dries up**: z-score < -1.0
- **Volatility spike**: ATR > 9% (1.5x threshold)
- **Max hold time**: 6 hours (momentum trades act faster)

### 4. Backtest Engine ([walkforward.py](core_engine/backtest/walkforward.py))

**New method**: `_evaluate_trade_with_exit_strategy()`
- Iterates through each price point after entry
- Calls strategy's `should_close_position()` at each timestamp
- Exits immediately when strategy signals to close
- Falls back to last available price if no exit signal

**Updated behavior**:
- `window_hours` parameter now represents maximum holding time (safety limit)
- Actual exit time is determined by strategy logic
- Trade results include `exit_reason` in metadata ('strategy_signal' or 'max_time')

### 5. Design Documentation ([design.md](design.md))

Updated sections:
- Title changed to "Short-Term, Low-Risk" (from "4h Horizon")
- Added principle #6: "Strategies control their own exits"
- Expanded strategy interface to include `should_close_position()`
- Updated evaluation approach description
- Added exit condition examples for baseline strategies
- Clarified that `window_hours` is now a maximum limit

## Benefits

1. **Flexibility**: Each strategy can optimize its own holding period
2. **Risk control**: Strategies can implement custom stop-losses and take-profits
3. **Market adaptation**: Exit based on technical signals, not arbitrary time
4. **Short-term focus**: Typical holds < 8 hours, maintaining low-risk profile
5. **Strategy diversity**: Different strategies can have different time horizons within the short-term scope

## Philosophy

The system remains focused on **short-term, low-risk trading opportunities**, but now:
- Strategies have full control over position lifecycle
- Holding time adapts to market conditions
- Exit logic is transparent and strategy-specific
- Time-based exits are optional (used as safety fallbacks)

## Next Steps (Optional)

Consider implementing:
1. Trailing stops in strategy exit logic
2. Partial position exits (scale out at different targets)
3. Re-entry logic after early exits
4. Strategy-specific maximum position limits
5. Metrics tracking average holding times per strategy
