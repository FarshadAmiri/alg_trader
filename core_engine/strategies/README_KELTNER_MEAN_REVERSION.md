# Keltner Channel Mean Reversion Strategy

## Overview
The Keltner Channel Mean Reversion strategy is a statistical trading system that exploits extreme price extensions and the tendency of prices to revert to the mean. By using volatility-adjusted channels around an EMA, this strategy identifies overbought/oversold conditions and trades the snapback to equilibrium. It's particularly effective in ranging and moderately trending markets where price oscillates around a moving average.

## Strategy Logic

### Core Concept
**"Prices that deviate excessively from the mean tend to revert back"**

The Keltner Channel creates a statistical envelope around price:
- **Middle Line**: 20-period EMA (the "mean")
- **Upper Band**: EMA + (2.0 × ATR)
- **Lower Band**: EMA - (2.0 × ATR)

When price extends beyond these bands, it's statistically "too far" and likely to snap back.

### Keltner Channel Construction

#### Components
1. **Basis (Middle Line)**: 20-period EMA
   - Represents fair value, equilibrium price
   - Dynamic support/resistance
   
2. **ATR Multiplier**: 2.0 (standard deviation equivalent)
   - Controls channel width
   - Adjusts for volatility automatically
   
3. **ATR Period**: 10-14 periods
   - Measures recent volatility
   - Wider channels in volatile periods

#### Why Keltner vs Bollinger Bands?
- **Keltner**: Uses ATR (true range), smoother, fewer false signals
- **Bollinger**: Uses standard deviation, more reactive, noisier
- **Crypto Markets**: ATR better captures gaps and volatility spikes

### Entry Rules

#### Long Entry (Oversold Reversion)
1. **Extreme Condition**:
   - Price closes **below** lower Keltner band
   - Or candlestick wick touches/pierces lower band
   - Price is "stretched" below fair value
   
2. **Mean Reversion Signal**:
   - **Trigger A**: Next candle closes back **inside** channel (above lower band)
   - **Trigger B**: Bullish reversal pattern at lower band (hammer, engulfing)
   - **Trigger C**: RSI < 30 turning upward
   
3. **Confirmation Filters**:
   - No major bearish trend (EMA not steeply declining)
   - Volume spike on reversal candle (>1.3x average)
   - Price above major support level
   - Multiple timeframe alignment (higher TF not bearish)
   
4. **Entry Execution**:
   - Enter market order on confirmation candle close
   - Or limit order at lower band for better price

#### Short Entry (Overbought Reversion)
1. **Extreme Condition**:
   - Price closes **above** upper Keltner band
   - Or candlestick wick touches/pierces upper band
   - Price is "stretched" above fair value
   
2. **Mean Reversion Signal**:
   - **Trigger A**: Next candle closes back **inside** channel (below upper band)
   - **Trigger B**: Bearish reversal pattern at upper band (shooting star, engulfing)
   - **Trigger C**: RSI > 70 turning downward
   
3. **Confirmation Filters**:
   - No major bullish trend (EMA not steeply rising)
   - Volume spike on reversal candle
   - Price below major resistance level
   - Multiple timeframe check
   
4. **Entry Execution**:
   - Enter market order on confirmation candle close
   - Or limit order at upper band for better price

### Exit Rules

#### Stop Loss
**Fixed Stop** (Recommended):
- **Long**: 1.5 ATR below entry or below recent swing low
- **Short**: 1.5 ATR above entry or above recent swing high
- **Rationale**: If reversion fails, cut loss quickly
- **Typical**: 2-3% stop in crypto markets

**Channel-Based Stop** (Alternative):
- **Long**: Stop if price closes below lower band again (failed reversion)
- **Short**: Stop if price closes above upper band again

#### Take Profit
**Statistical Targets** (Primary Approach):
1. **Conservative**: Middle line (EMA) = 1:1.5 to 1:2 R:R
   - Price returns to mean
   - Highest probability target
   - Exit 50-70% of position here
   
2. **Aggressive**: Opposite band = 1:3 to 1:5 R:R
   - Full channel reversion
   - Lower probability
   - Trail stop for remaining 30-50%

**Time-Based Exit** (Risk Management):
- If trade open > 48 hours without hitting target, close (mean reversion should be fast)
- Prevents turning MR trade into trend-following disaster

**Partial Exit Strategy** (Optimal):
- 50% at middle line (EMA)
- 30% at 75% channel width
- 20% trailing stop (below EMA or 1 ATR trailing)

### Position Sizing
- Risk: 1-1.5% per trade (conservative, more trades)
- Calculate based on ATR stop distance
- Reduce size in strong trends (mean reversion less reliable)
- Increase size in ranging markets

## Parameters

### Default Configuration
```python
{
    "ema_period": 20,           # Keltner basis (middle line)
    "atr_period": 10,           # ATR for channel width
    "atr_multiplier": 2.0,      # Channel width (2.0 = ~95% statistical)
    "rsi_period": 14,           # RSI confirmation
    "rsi_oversold": 30,         # Long trigger threshold
    "rsi_overbought": 70,       # Short trigger threshold
    "volume_threshold": 1.3,    # Volume spike confirmation
    "trend_filter": True,       # Avoid counter-major-trend trades
    "max_hold_bars": 48,        # Time-based exit (hours if 1H TF)
    "risk_per_trade": 0.015     # 1.5% risk
}
```

### Parameter Optimization

#### Tight Channels (Aggressive)
- EMA: 10-15, ATR Multiplier: 1.5
- More signals, tighter stops
- Higher win rate (65%+), smaller wins
- Best for: Ranging, low-volatility markets

#### Wide Channels (Conservative)
- EMA: 30-40, ATR Multiplier: 2.5-3.0
- Fewer signals, wider stops
- Lower win rate (45-50%), bigger wins
- Best for: Volatile, trending markets

#### Standard (Balanced - Recommended)
- EMA: 20, ATR Multiplier: 2.0
- Goldilocks zone
- 50-60% win rate, moderate R:R
- Works across most conditions

### ATR Period Impact
- **Short ATR (5-7)**: Reactive, more trades, noisier
- **Medium ATR (10-14)**: Balanced, standard
- **Long ATR (20-30)**: Smooth, fewer signals, cleaner

## Performance Characteristics

### Strengths
✅ **High Win Rate**: 55-70% (mean reversion naturally mean-reverting)
✅ **Defined Risk**: Clear stop placement (ATR-based)
✅ **Volatility Adjusted**: Channels adapt to market conditions
✅ **Visual Clarity**: Easy to see on charts (price at bands)
✅ **Statistical Edge**: Exploits natural price behavior
✅ **Frequent Signals**: Multiple opportunities per week
✅ **Works Ranging**: Excellent in sideways markets
✅ **Risk-Reward**: Often 1:2 or better to middle line

### Weaknesses
⚠️ **Trend Continuation**: Catastrophic in strong trends (price stays outside band)
⚠️ **False Reversals**: Price can pierce band multiple times before reverting
⚠️ **Requires Discipline**: Must exit at target (don't let winners reverse)
⚠️ **Time Sensitivity**: Slow reversions can reverse again before target
⚠️ **Whipsaw Risk**: Choppy markets = multiple small losses
⚠️ **Gap Risk**: Crypto gaps can blow through stops

### Expected Performance (Crypto Markets)
- **Win Rate**: 55-65%
- **Profit Factor**: 1.8-2.5
- **Average Winner**: 3-5% (to middle line)
- **Average Loser**: 1.5-2.5%
- **Max Drawdown**: 10-15%
- **Signal Frequency**: 5-12 per month per symbol
- **Best Markets**: Ranging, moderate trends with oscillations

## Timeframe Recommendations

### Optimal Timeframes
1. **1 Hour**: Best for active trading, quick reversions
2. **4 Hour**: Swing trading, more reliable signals
3. **15 Minute**: Scalping (requires tight risk management)
4. **1 Day**: Position trades, very high probability setups

### Multi-Timeframe Filter
**Critical Enhancement**: Always check higher timeframe
- **Trading TF**: 1H Keltner (entry signals)
- **Trend TF**: 4H or 1D (trend direction)
- **Rule**: Only take reversions aligned with higher TF
  - If 4H uptrend, only take 1H long reversions (buy dips)
  - If 4H downtrend, only take 1H short reversions (sell rips)
  - If 4H ranging, take both directions

**Example**:
- 1D chart: BTC in uptrend (above 1D EMA)
- 1H chart: Price pierces lower Keltner band
- **Action**: Long (buying dip in uptrend) ✅
- **Avoid**: Short (counter to 1D trend) ❌

## Market Conditions

### Best Performance
- **Ranging Markets**: Price oscillates within defined range
- **Mean-Reverting Phases**: After trend exhaustion
- **Moderate Volatility**: Enough movement but not panic
- **Choppy Trends**: Trends with frequent pullbacks
- **Altcoins**: Higher volatility = bigger band extensions
- **After News Fade**: Price snaps back post-spike

### Poor Performance
- **Strong Trends**: Price rides upper/lower band for extended periods
- **Breakout Phases**: Price establishes new range (old mean invalid)
- **Extreme Volatility**: ATR widens, signals less reliable
- **Low Liquidity**: Slippage on reversals
- **Cascading Liquidations**: Price crashes through all support

### Market Regime Detection
Implement **Trend Strength Filter**:
```python
# ADX or EMA slope
if ADX > 30:  # Strong trend
    skip_mean_reversion()  # Don't fight trend
elif ADX < 20:  # Ranging
    full_confidence_trading()  # Perfect for MR
```

## Risk Management

### Key Risk Controls

#### Trend Filter (Critical)
1. **EMA Slope**: Don't trade against steep EMA angles
2. **ADX Check**: ADX > 30 = skip mean reversion
3. **Higher Timeframe**: Must align with HTF direction or be neutral
4. **Swing Structure**: Price should be making swing highs/lows (not runaway)

#### Entry Quality
1. **Band Penetration**: Price must clearly touch/close outside band
2. **Reversal Confirmation**: Wait for close back inside (don't fade first touch)
3. **Volume**: Spike on reversal candle (shows buying/selling pressure)
4. **RSI Confirmation**: RSI turning from extreme (30/70)
5. **Candlestick Pattern**: Reversal patterns add confidence

#### Position Management
1. **Initial Risk**: 1-1.5% per trade
2. **Partial Exits**: Lock profit at middle line (50% off)
3. **Time Stop**: Exit if > 48 hours (mean reversion failed)
4. **Max Positions**: 3-4 concurrent (diversify across symbols)
5. **No Pyramiding**: Don't add to losers (one entry, done)

### Disaster Prevention
**"What if price keeps going?"** (Trend continuation scenario)
- Stop loss MUST be honored (no moving stops back)
- Accept loss, don't revenge trade
- Check trend filters before next trade
- If 3 consecutive stops, pause (market regime changed)

## Enhancements & Variations

### Keltner + Bollinger Squeeze
- Overlay Bollinger Bands on Keltner Channels
- When BBands inside Keltner = low volatility squeeze
- Trade breakouts from squeeze, then mean revert back
- **Hybrid**: Breakout + Mean Reversion system

### Keltner + Volume Profile
- Identify high-volume nodes within Keltner Channel
- Only trade reversions that find support/resistance at volume clusters
- Dramatically increases probability
- Professional institutional approach

### Keltner + Fibonacci
- When price at lower band, check if also at Fib support (0.382, 0.5, 0.618)
- Confluence = higher probability reversion
- Combine statistical (Keltner) with structural (Fib)

### Keltner + RSI Divergence
- Price at lower band + Bullish RSI divergence = ultra-high probability long
- Price at upper band + Bearish RSI divergence = ultra-high probability short
- Combining two mean-reversion signals

### Adaptive Keltner
- Adjust ATR multiplier based on market regime
- Trending: 2.5-3.0 (wider channels, fewer signals)
- Ranging: 1.5-2.0 (tighter channels, more signals)
- Use ADX to determine regime automatically

### Multi-Target Exits
```python
# Example sophisticated exit
if price_at_middle_line:
    close_percent(50)  # Lock half
    move_stop_to_breakeven()
    
if price_at_75_percent_channel:
    close_percent(30)  # Take more
    trail_stop(below_ema, atr=1.0)
    
if price_at_opposite_band:
    close_all()  # Full reversion, exit
```

## Backtesting Notes

### Data Requirements
- Minimum: 50 bars (for 20 EMA + ATR calculations)
- Recommended: 500+ bars for statistics
- Must Include: OHLC (for ATR true range calculation)
- Volume: Optional but improves filtering

### Critical Backtesting Considerations
1. **Look-Ahead Bias**: Don't use future candle close in signal
   - Signal triggers on candle N
   - Enter at candle N+1 open (realistic)
   
2. **Slippage**: Mean reversions can be fast, model 0.1-0.2% slippage
   
3. **Partial Exits**: Accurately model 50% at middle, 50% trailing
   
4. **Time Stops**: Ensure max hold period enforced
   
5. **Regime Filtering**: Critical to exclude trending phases

### Walk-Forward Optimization
- Optimize ATR multiplier on 60% data
- Test on 40% out-of-sample
- Should see consistent performance
- ATR 1.5-2.5 range should all work (robustness)

### Red Flags (Overfitting)
- Win rate > 75% (unrealistic for MR)
- Single parameter value works, nearby fail
- Performance degrades sharply out-of-sample
- Zero drawdown periods (too good to be true)

## Implementation Checklist

### Required Features
- [ ] EMA calculation (20-period basis)
- [ ] ATR calculation (10-14 period)
- [ ] Keltner Channel construction (upper/lower bands)
- [ ] Band penetration detection
- [ ] Reversal confirmation (close inside band)
- [ ] RSI calculation (optional filter)
- [ ] Volume analysis (spike detection)
- [ ] Trend filter (ADX or EMA slope)

### Required Risk Components
- [ ] ATR-based stop loss (1.5 ATR)
- [ ] Position sizing (risk-based)
- [ ] Partial exit logic (multiple targets)
- [ ] Time-based stop (max hold 48 bars)
- [ ] Trend regime detection
- [ ] Maximum concurrent positions

### Strategy Class Methods
- [ ] `compute_features()`: EMA, ATR, Keltner bands, RSI, volume
- [ ] `detect_band_penetration()`: Price outside channel
- [ ] `detect_reversion_signal()`: Close back inside + confirmation
- [ ] `check_trend_filter()`: ADX or EMA slope check
- [ ] `should_enter()`: All entry conditions
- [ ] `should_exit()`: Multiple exit scenarios (target, stop, time)
- [ ] `calculate_position_size()`: Risk % based on ATR stop

## Visual Pattern Recognition

### Perfect Long Setup
```
Upper Band: ________________
               ↗ Price rejects here
Middle (EMA): ___↗____↗____↗___ (fair value)
              ↙ Reversal
Lower Band: ___↓____________
           ↓ Price pierces (oversold)
           ↑ Entry: close back inside
```

### Keltner Channel in Range
```
Price oscillating between bands (ideal)

Upper Band: ___~~~___~~~___
              ↗   ↘   ↗   ↘  (Short here)
Middle:     ___---___---___
              ↙   ↗   ↙   ↗  (Long here)
Lower Band: ___~~~___~~~___

Multiple mean reversion trades
```

### Keltner Channel in Trend (Avoid)
```
Price riding upper band (strong uptrend)

Upper Band: _____↗↗↗↗↗↗↗ (Price here)
Middle:     ___↗↗↗↗↗↗↗ (Ignore)
Lower Band: _↗↗↗↗↗↗↗

Don't short! Trend too strong.
```

## Psychology & Discipline

### Mental Edge
- **Contrarian Trading**: Requires courage (buying fear, selling greed)
- **Trust Statistics**: Mean reversion is mathematical law
- **Accept Losses**: Trends happen, take stop, move on
- **Quick Profits**: Take money at target (don't get greedy)

### Common Mistakes
1. **Holding Winners Too Long**: Reversion can reverse back
   - Fix: Strict target exits, partial profits
   
2. **Fading Strong Trends**: Shorting runaway markets
   - Fix: Trend filter, ADX check, HTF alignment
   
3. **Moving Stops**: Price near stop, move it back
   - Fix: Set stop, honor stop, never move against position
   
4. **Ignoring Time**: Holding losing MR trade for days
   - Fix: 48-hour max hold, exit if no reversion

## References & Resources

### Academic Foundation
- **Mean Reversion**: Documented in equities since 1980s (Poterba, Summers)
- **Keltner Channels**: Invented by Chester Keltner (1960), refined by Linda Bradford Raschke
- **Statistical Edge**: Prices revert to mean 65-75% of time in sideways markets

### Professional Usage
- Market makers use mean reversion for inventory management
- Stat arb hedge funds exploit mean reversion across pairs
- High-frequency traders capture micro-reversions

### Crypto Applications
- Effective in altcoin ranging phases (2018-2019 bear market)
- Used by crypto market makers on exchanges
- Retail traders favor for visual clarity

### Modern Research
- Keltner superior to Bollinger in high-volatility assets (2015 study)
- ATR-based channels adapt better to regime changes
- Combining with volume profile increases edge (2018 analysis)

## Code Structure (Planned)

```python
class KeltnerMeanReversionStrategy(BaseStrategy):
    """
    Keltner Channel mean reversion strategy.
    
    Trades price extensions beyond volatility-adjusted bands,
    entering on reversion signals back to middle line (EMA).
    Requires trend filtering to avoid counter-trend disasters.
    
    Parameters:
        ema_period: Keltner basis period (default: 20)
        atr_period: ATR calculation period (default: 10)
        atr_multiplier: Channel width multiplier (default: 2.0)
        trend_filter: Enable ADX/slope filtering (default: True)
    """
    
    def __init__(self, parameters=None):
        self.preferred_timeframe = '1h'
        self.evaluation_mode = 'every_bar'
        self.max_hold_hours = 48.0
        # ... implementation
        
    def compute_keltner_bands(self, data):
        """
        Calculate Keltner Channel components.
        
        Returns:
            middle: EMA (fair value)
            upper: EMA + (ATR × multiplier)
            lower: EMA - (ATR × multiplier)
        """
        pass
        
    def detect_band_penetration(self, price, bands):
        """
        Check if price is outside Keltner bands.
        
        Returns:
            'above_upper': Overbought
            'below_lower': Oversold
            'inside': Normal
        """
        pass
        
    def detect_reversion_signal(self, current_bar, previous_bar, bands):
        """
        Confirm mean reversion trigger.
        
        Checks:
        - Previous bar outside band
        - Current bar closes inside band
        - Volume confirmation
        - RSI turning
        """
        pass
```

---

**Status**: 📋 Documentation Complete - Implementation Pending
**Complexity**: ⭐⭐⭐ Medium
**Reliability**: ⭐⭐⭐⭐ High (in right conditions)
**Market Suitability**: Ranging/oscillating markets (40% of crypto conditions)
**Win Rate**: 55-65% (Statistical advantage)
**Critical Success Factor**: Trend filtering (avoid trading against strong trends)
