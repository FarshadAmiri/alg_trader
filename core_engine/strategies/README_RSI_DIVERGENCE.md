# RSI Divergence Strategy

## Overview
RSI Divergence is a powerful counter-trend strategy that identifies potential reversals by detecting disagreements between price action and the Relative Strength Index (RSI) momentum indicator. This classic technical analysis pattern has been used successfully since the 1970s and remains highly effective in crypto markets.

## Strategy Logic

### Core Concept
**Divergence** occurs when price makes a new high/low but RSI fails to confirm, signaling weakening momentum and potential reversal.

### Types of Divergence

#### Bullish Divergence (Long Entry)
- **Price**: Makes lower low
- **RSI**: Makes higher low
- **Interpretation**: Selling pressure weakening, potential upside reversal
- **Context**: Occurs in downtrends or at support levels

#### Bearish Divergence (Short Entry)
- **Price**: Makes higher high  
- **RSI**: Makes lower high
- **Interpretation**: Buying pressure weakening, potential downside reversal
- **Context**: Occurs in uptrends or at resistance levels

#### Hidden Divergence (Trend Continuation)
- **Bullish Hidden**: Price higher low, RSI lower low → Uptrend continues
- **Bearish Hidden**: Price lower high, RSI higher high → Downtrend continues

### Entry Rules

#### Long Entry (Bullish Divergence)
1. **Identify Downswing**: Price makes 2+ consecutive lower lows
2. **RSI Pattern**: RSI makes higher low during same period
3. **RSI Level**: Second RSI low is between 20-40 (oversold region)
4. **Confirmation**: Price breaks above recent swing high OR RSI crosses 50
5. **Volume**: Volume increasing on reversal confirmation
6. **Support**: Price near significant support level (optional)

#### Short Entry (Bearish Divergence)
1. **Identify Upswing**: Price makes 2+ consecutive higher highs
2. **RSI Pattern**: RSI makes lower high during same period
3. **RSI Level**: Second RSI high is between 60-80 (overbought region)
4. **Confirmation**: Price breaks below recent swing low OR RSI crosses 50
5. **Volume**: Volume increasing on reversal confirmation
6. **Resistance**: Price near significant resistance level (optional)

### Exit Rules

#### Stop Loss
- **Long**: Below the divergence low (price low that formed the pattern)
- **Short**: Above the divergence high (price high that formed the pattern)
- **Buffer**: Add 1-2% buffer for volatility
- **Time Stop**: Exit if no movement within 24-48 hours

#### Take Profit
1. **Target 1**: Previous swing high/low (50% position exit)
2. **Target 2**: RSI opposite extreme (RSI 70 for longs, RSI 30 for shorts)
3. **Target 3**: Fibonacci extensions (1.618x initial move)
4. **Trailing**: Move stop to breakeven after Target 1 hit

### Position Sizing
- Risk: 1.5-2% per trade
- Size based on stop loss distance
- Reduce size if multiple divergences active

## Parameters

### Default Configuration
```python
{
    "rsi_period": 14,              # RSI calculation period
    "rsi_oversold": 30,            # Oversold threshold
    "rsi_overbought": 70,          # Overbought threshold
    "divergence_lookback": 50,     # Bars to search for divergence
    "min_swing_distance": 10,      # Minimum bars between swing points
    "confirmation_required": True,  # Wait for breakout confirmation
    "support_resistance_check": True  # Filter by S/R levels
}
```

### Parameter Optimization Ranges
- **RSI Period**: 9-21 (shorter = more sensitive, longer = smoother)
- **Oversold/Overbought**: 20-40 / 60-80 (adjust for volatility)
- **Lookback**: 30-100 bars (affects pattern detection)

## Performance Characteristics

### Strengths
✅ **High Win Rate**: 60-70% when properly filtered
✅ **Excellent R:R**: Average 1:2 to 1:4 risk-reward ratio
✅ **Early Reversal**: Catches turns before they're obvious
✅ **Works in Ranges**: Perfect for sideways/consolidating markets
✅ **Clear Visual**: Easy to spot on charts
✅ **Time-Tested**: Proven pattern since 1970s
✅ **Multiple Confirmations**: Various filters reduce false signals

### Weaknesses
⚠️ **Subjective Pattern**: Swing high/low identification can vary
⚠️ **False Divergences**: Not all divergences lead to reversals
⚠️ **Trend Strength**: Fails in very strong trends (trend continuation overpowers)
⚠️ **Whipsaws**: Can get stopped out in volatile markets
⚠️ **Patience Required**: Setup doesn't occur frequently
⚠️ **Lagging**: Confirmation can delay entry, missing best prices

### Expected Performance (Crypto Markets)
- **Win Rate**: 60-70%
- **Profit Factor**: 2.0-3.0
- **Average Winner**: 3-5%
- **Average Loser**: 1.5-2.5%
- **Max Drawdown**: 10-15%
- **Signal Frequency**: 2-5 per month per symbol
- **Best Markets**: Ranging/consolidating conditions

## Timeframe Recommendations

### Optimal Timeframes
1. **4 Hour**: Best balance of reliability and opportunity
2. **1 Hour**: Good for active trading, more signals
3. **1 Day**: Highest reliability, fewer signals, swing trading
4. **15 Minute**: Scalping, requires very tight risk management

### Multi-Timeframe Approach
- **Higher TF**: Identify trend direction (1D/4H)
- **Trading TF**: Find divergence setups (1H/15m)
- **Rule**: Only trade divergences aligned with higher TF trend reversal

## Market Conditions

### Best Performance
- **Ranging Markets**: Sideways consolidation, mean reversion works well
- **After Strong Moves**: Exhaustion reversals at extremes
- **At Support/Resistance**: Divergence + S/R = high probability
- **Volatility Expansion**: After compression, reversals are sharp
- **Overbought/Oversold**: RSI extremes increase pattern reliability

### Poor Performance
- **Strong Trends**: Momentum overwhelms divergence signals
- **Low Volatility**: Small ranges, unclear swing points
- **News Events**: Fundamentals override technical patterns
- **Flash Crashes**: Abnormal price action invalidates patterns

## Risk Management

### Key Risk Controls
1. **Confirmation Filter**: Don't enter on divergence alone, wait for breakout
2. **Support/Resistance**: Only trade near key levels
3. **Trend Alignment**: Prefer divergences that align with higher timeframe
4. **Max Positions**: Limit to 2-3 divergence trades simultaneously
5. **Stop Loss Discipline**: Never move stop further away

### Advanced Filters

#### False Divergence Reduction
- **Volume Confirmation**: Rising volume on reversal validates divergence
- **Multiple Timeframes**: Divergence on 2+ timeframes = stronger
- **MACD Divergence**: Confirm RSI divergence with MACD divergence
- **Price Structure**: Divergence at swing high/low more reliable than mid-range

#### Entry Refinement
- **Wait for Candle Close**: Confirm divergence at bar close, not mid-bar
- **Breakout Entry**: Enter on break of divergence high/low, not at formation
- **RSI Center Cross**: Enter when RSI crosses 50 (momentum shift)

## Enhancements & Variations

### RSI Divergence + Volume
- Require volume spike on reversal confirmation
- Volume profile analysis for support/resistance
- Increases win rate to 70-75%

### RSI Divergence + Chart Patterns
- Combine with head & shoulders, double tops/bottoms
- Pattern + divergence = very high probability
- Example: Double bottom with bullish divergence

### Hidden Divergence for Continuation
- Trade hidden divergences in direction of trend
- Lower risk, captures trend continuation
- Works in crypto uptrends very well

### Multi-Oscillator Divergence
- Confirm RSI divergence with MACD, Stochastic, CCI
- Multiple indicators agreeing = highest probability
- Reduces false signals by 50%+

## Backtesting Notes

### Data Requirements
- Minimum: 200 bars for swing identification
- Recommended: 1000+ bars for statistical significance
- Need: High, Low, Close for swing detection

### Challenges in Backtesting
- **Swing Point Subjectivity**: Need clear algorithm for pivot detection
- **Confirmation Logic**: Define exact entry trigger
- **Visual vs Code**: Patterns obvious to eye, harder to code

### Robustness Checks
- Test across different pivot detection methods
- Vary confirmation requirements
- Test on trending vs ranging market subsets separately
- Parameter sensitivity: Small changes shouldn't drastically affect results

## Implementation Checklist

### Required Features
- [ ] RSI calculation (14-period standard)
- [ ] Swing high/low detection (pivot points)
- [ ] Divergence pattern recognition
- [ ] Support/Resistance level identification
- [ ] Volume analysis
- [ ] Breakout/breakdown detection

### Required Risk Components
- [ ] Swing-based stop loss calculation
- [ ] Multiple take-profit targets
- [ ] Trailing stop implementation
- [ ] Position sizing based on stop distance

### Strategy Class Methods
- [ ] `compute_features()`: Calculate RSI, swings, S/R
- [ ] `detect_divergence()`: Identify bullish/bearish patterns
- [ ] `confirm_divergence()`: Check confirmation criteria
- [ ] `should_enter()`: Entry with all filters
- [ ] `should_exit()`: Multiple exit targets
- [ ] `calculate_position_size()`: Risk-based sizing

## Divergence Detection Algorithm

### Pseudo-Code
```python
def detect_bullish_divergence(price, rsi, lookback=50):
    """
    1. Find price lows in lookback period (local minima)
    2. Find corresponding RSI values at those lows
    3. Check if:
       - Price: L2 < L1 (lower low)
       - RSI: R2 > R1 (higher low)
       - Both RSI values < 40 (oversold region)
    4. Return divergence if conditions met
    """
    pass

def confirm_divergence(divergence, current_bar):
    """
    1. Check if price broke above divergence swing high
    OR
    2. Check if RSI crossed above 50
    
    Additional filters:
    - Volume > average
    - Near support level
    """
    pass
```

## References & Resources

### Original Work
- J. Welles Wilder Jr. - "New Concepts in Technical Trading Systems" (1978)
- Introduced RSI indicator

### Academic Validation
- Divergence patterns show statistical edge (2003, Balsara study)
- Technical Analysis of Stocks & Commodities articles (1980s-2020s)

### Modern Application
- Used by institutional traders for reversal timing
- Popular in crypto trading since 2017
- Featured in major trading platforms (TradingView, etc.)

## Code Structure (Planned)

```python
class RSIDivergenceStrategy(BaseStrategy):
    """
    RSI Divergence mean-reversion strategy.
    
    Detects bullish/bearish divergences between price and RSI,
    enters on confirmation, targets previous swing extremes.
    
    Parameters:
        rsi_period: RSI calculation window (default: 14)
        divergence_lookback: Bars to scan for divergence (default: 50)
        confirmation_required: Wait for breakout (default: True)
    """
    
    def __init__(self, parameters=None):
        self.preferred_timeframe = '1h'
        self.evaluation_mode = 'every_bar'
        self.max_hold_hours = 72.0
        # ... implementation
```

## Visual Examples

### Bullish Divergence Setup
```
Price:     \    /\    /\
           ↓   ↓  ↓  ↓
          L1      L2  ← Lower Low

RSI:       \      /
           ↓     ↓
          30    35    ← Higher Low (Divergence!)

Entry: When price breaks above point between L1 and L2
Stop: Below L2
Target: Previous swing high
```

### Bearish Divergence Setup
```
Price:     /\    /\
          ↑  ↑  ↑  ↑
         H1     H2  ← Higher High

RSI:      /\    
         ↑  ↑
        75  70     ← Lower High (Divergence!)

Entry: When price breaks below point between H1 and H2
Stop: Above H2
Target: Previous swing low
```

---

**Status**: 📋 Documentation Complete - Implementation Pending
**Complexity**: ⭐⭐⭐ Medium
**Reliability**: ⭐⭐⭐⭐ High
**Market Suitability**: Ranging/consolidating markets (40% of crypto conditions)
