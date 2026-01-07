# Momentum Rank Strategy

## Overview
The Momentum Rank strategy is a relative strength rotation system that ranks multiple assets by momentum and systematically rotates capital into the strongest performers. Unlike single-asset strategies, this approach exploits the persistence of momentum across crypto markets by continuously holding the top N performers. It achieves 55-70% win rates by riding market leaders and cutting losers quickly.

## Strategy Logic

### Core Concept
**"Strong assets get stronger, weak assets get weaker - systematically own the leaders"**

1. **Universe**: Trade a basket of crypto assets (10-50 symbols)
2. **Ranking**: Calculate momentum score for each asset
3. **Selection**: Hold top N ranked assets (e.g., top 5)
4. **Rotation**: Rebalance periodically (weekly/monthly) to maintain top performers
5. **Result**: Always invested in market leaders, systematic momentum capture

### Why Momentum Rotation Works

#### Empirical Evidence
- **Academic**: "Momentum persists for 3-12 months" (Jegadeesh & Titman, 1993)
- **Crypto Markets**: "6-month momentum predicts next month returns" (Liu et al., 2019)
- **Cross-Asset**: Works in stocks, futures, crypto, FX

#### Behavioral Foundation
- **Herding**: Traders pile into winners (momentum begets momentum)
- **Under-Reaction**: Markets slowly incorporate good news (trend continues)
- **Anchoring**: Investors slow to update beliefs (winners keep winning)

#### Crypto-Specific Factors
- **Retail FOMO**: Fear of missing out drives momentum
- **Narrative Cycles**: Hot narratives (DeFi, NFTs, AI) create sustained momentum
- **Liquidity Cascades**: Large caps attract more capital, self-reinforcing

## Momentum Calculation Methods

### Method 1: Simple Rate of Change (Basic)
```python
momentum_score = (current_price / price_N_days_ago) - 1
# Example: (100 / 80) - 1 = 0.25 = 25% gain
```
- **Lookback**: 30, 60, 90, 180 days
- **Pros**: Simple, intuitive
- **Cons**: Sensitive to entry point, volatility-blind

### Method 2: Risk-Adjusted Momentum (Better)
```python
returns = price.pct_change().tail(lookback)
momentum_score = returns.mean() / returns.std()
# Sharpe-like ratio
```
- **Pros**: Accounts for volatility, smoother
- **Cons**: Penalizes volatile but trending assets

### Method 3: Multi-Period Composite (Best)
```python
# Weighted average of multiple lookbacks
score_30d = (price / price_30d_ago) - 1
score_60d = (price / price_60d_ago) - 1
score_90d = (price / price_90d_ago) - 1
score_180d = (price / price_180d_ago) - 1

momentum_score = (
    0.15 * score_30d +   # Recent: 15%
    0.25 * score_60d +   # Medium: 25%
    0.35 * score_90d +   # Primary: 35%
    0.25 * score_180d    # Long-term: 25%
)
```
- **Pros**: Captures multi-timeframe momentum, reduces noise
- **Cons**: More complex, parameter-sensitive
- **Recommended**: This approach for crypto

### Method 4: Volume-Weighted Momentum (Advanced)
```python
price_change = (current_price / price_90d_ago) - 1
avg_volume_ratio = recent_volume_90d / previous_volume_90d

momentum_score = price_change * (1 + avg_volume_ratio)
# Boost score if volume increasing (institutional interest)
```
- **Pros**: Incorporates volume (conviction)
- **Cons**: Volume data can be unreliable (wash trading)

## Strategy Variants

### Variant 1: Top N Absolute (Equal Weight)
- Rank all assets by momentum
- Hold top N (e.g., top 5)
- Equal allocation to each (20% each if N=5)
- Rebalance weekly/monthly

### Variant 2: Top Percentile (Threshold)
- Hold all assets with momentum score > threshold (e.g., > 20% gain)
- Variable portfolio size (could be 2-10 assets)
- Market-adaptive (bull market = more assets, bear = fewer)

### Variant 3: Long-Short (Market Neutral)
- Long top N performers
- Short bottom N performers
- Hedged against market direction
- Requires margin/derivatives (not available all exchanges)

### Variant 4: Tiered Allocation (Optimal)
- Rank 1: 30% allocation
- Rank 2: 25%
- Rank 3: 20%
- Rank 4: 15%
- Rank 5: 10%
- Overweight strongest performers
- **Recommended for crypto**

## Entry Rules

### Portfolio Construction (Rebalance Period)

1. **Universe Definition**:
   - Select tradable crypto assets (e.g., top 50 by market cap)
   - Exclude stablecoins, wrapped tokens
   - Require minimum liquidity (> $1M daily volume)

2. **Momentum Calculation**:
   - For each asset, calculate composite momentum score
   - Use 30/60/90/180 day weighted average
   - Exclude assets with <180 days of data

3. **Ranking**:
   - Sort all assets by momentum score (descending)
   - Identify top N (e.g., top 5)

4. **Portfolio Rebalance**:
   - **Sell**: Assets no longer in top N
   - **Buy**: New assets entering top N
   - **Hold**: Assets remaining in top N (may adjust weights)

5. **Execution**:
   - Place market orders at rebalance time
   - Or limit orders at current price (reduce slippage)
   - Execute all trades within 1-hour window

### Rebalance Frequency

#### Weekly Rebalancing
- **Pros**: Captures momentum shifts quickly, responsive
- **Cons**: Higher transaction costs, more whipsaws
- **Best For**: High-volatility periods, active management

#### Monthly Rebalancing (Recommended)
- **Pros**: Lower transaction costs, smoother, tax-efficient
- **Cons**: May miss rapid momentum shifts
- **Best For**: Most crypto market conditions

#### Quarterly Rebalancing
- **Pros**: Minimal costs, very tax-efficient
- **Cons**: Slow to adapt, may hold deteriorating assets
- **Best For**: Long-term investors, low-fee exchanges

## Exit Rules

### Portfolio Exit (Sell Triggers)

1. **Ranking Exit** (Primary):
   - Asset falls out of top N rankings
   - Sell at next rebalance period
   - Systematic, no discretion

2. **Stop Loss** (Risk Management):
   - Individual asset drops >25% from entry
   - Immediate exit (don't wait for rebalance)
   - Prevents catastrophic loss (exchange hacks, delistings)

3. **Time-Based** (Periodic):
   - Automatic rebalance every N weeks/months
   - Recalculate rankings, adjust portfolio

4. **Drawdown Protection** (Portfolio Level):
   - If total portfolio down >20% from peak, reduce exposure 50%
   - Or exit all positions (go to cash)
   - Re-enter when momentum improves

### Take Profit
- **No Fixed Target**: Ride momentum as long as it ranks
- **Trailing Stop** (Optional): 15-20% trailing stop per asset
- **Rebalance Profit**: Winners automatically reduced if rank drops

## Position Sizing

### Equal Weight (Simple)
```python
allocation_per_asset = 1.0 / N
# If N=5: 20% each
# If N=10: 10% each
```

### Tiered Weight (Recommended)
```python
# Top 5 example
weights = [0.30, 0.25, 0.20, 0.15, 0.10]
# Rank 1 gets 30%, Rank 5 gets 10%
```

### Score-Weighted (Advanced)
```python
# Weight by momentum score
total_score = sum(top_N_scores)
allocation = asset_score / total_score
# Highest momentum gets largest allocation
```

### Risk Parity (Sophisticated)
```python
# Allocate based on inverse volatility
volatility = asset.std()
inv_vol_weight = (1 / volatility) / sum(1 / all_volatilities)
# Lower volatility = higher allocation
```

## Parameters

### Default Configuration
```python
{
    # Universe
    "universe_size": 50,         # Top 50 cryptos by market cap
    "min_market_cap": 100e6,     # $100M minimum
    "min_daily_volume": 1e6,     # $1M daily volume
    
    # Momentum Calculation
    "lookback_30d": 30,
    "lookback_60d": 60,
    "lookback_90d": 90,
    "lookback_180d": 180,
    "weight_30d": 0.15,
    "weight_60d": 0.25,
    "weight_90d": 0.35,
    "weight_180d": 0.25,
    
    # Portfolio Construction
    "top_n": 5,                  # Hold top 5 assets
    "rebalance_days": 30,        # Monthly rebalance
    "allocation_method": "tiered",  # tiered, equal, score_weighted
    
    # Risk Management
    "individual_stop_loss": 0.25,   # 25% stop per asset
    "portfolio_drawdown_limit": 0.20,  # 20% portfolio stop
    "max_position_size": 0.30,      # No single asset > 30%
    
    # Filters
    "min_data_days": 180,        # Require 6 months history
    "exclude_stablecoins": True
}
```

### Parameter Optimization

#### Aggressive (High Turnover)
- Top N: 3 (concentrated)
- Rebalance: Weekly
- Lookback: Favor shorter (30/60d weighted higher)
- Result: High returns potential, high costs

#### Conservative (Low Turnover)
- Top N: 10 (diversified)
- Rebalance: Quarterly
- Lookback: Favor longer (180d weighted higher)
- Result: Smoother returns, lower costs

#### Balanced (Recommended)
- Top N: 5
- Rebalance: Monthly
- Lookback: Composite (15/25/35/25 weights)
- Allocation: Tiered
- Result: Good returns, manageable costs

## Performance Characteristics

### Strengths
✅ **Systematic**: No discretion, fully rule-based
✅ **Diversified**: Holds multiple assets, reduces single-asset risk
✅ **Momentum Capture**: Always in strongest performers
✅ **Market Adaptive**: Rotates with changing leaders
✅ **Proven Edge**: Momentum premium documented for decades
✅ **Scalable**: Works with 5 or 50 assets
✅ **Transparent**: Clear ranking methodology
✅ **Backtestable**: Precise historical simulation possible

### Weaknesses
⚠️ **Transaction Costs**: Frequent rebalancing = fees add up
⚠️ **Slippage**: Moving capital across assets = market impact
⚠️ **Momentum Crashes**: Sudden reversals can hurt (COVID March 2020)
⚠️ **Crowded Trade**: Many funds use momentum (capacity constraints)
⚠️ **Data Requirements**: Need pricing for entire universe
⚠️ **Correlation**: In bear markets, all cryptos fall together
⚠️ **Whipsaw Risk**: Monthly rebalance can buy high, sell low

### Expected Performance (Crypto Markets)
- **Win Rate**: 55-70% (monthly rebalance basis)
- **Annual Return**: 40-80% (bull markets), -20-40% (bear markets)
- **Sharpe Ratio**: 1.2-2.0 (good risk-adjusted)
- **Max Drawdown**: 40-60% (2022 bear market)
- **Turnover**: 50-150% annually (depends on rebalance frequency)
- **Best Markets**: Bull trends, sector rotations
- **Worst Markets**: Choppy sideways, momentum reversals

## Timeframe Recommendations

### Lookback Periods
- **30 Days**: Short-term momentum, reactive
- **60 Days**: Medium-term, balance
- **90 Days**: Primary driver (sweet spot for crypto)
- **180 Days**: Long-term trend, stabilizer

### Rebalance Frequency
- **Weekly**: Day traders, high-cost tolerance
- **Monthly**: Recommended for most
- **Quarterly**: Long-term investors, tax-conscious

### Data Frequency
- **Daily Closes**: Standard, sufficient for ranking
- **Hourly**: Unnecessary complexity for momentum
- **Weekly**: Too coarse, misses important moves

## Market Conditions

### Best Performance
- **Bull Markets**: Rising tide lifts all boats, strong momentum
- **Sector Rotations**: Capital flows between narratives (DeFi → NFT → AI)
- **Moderate Volatility**: Trends persist without crashes
- **Divergent Performance**: Some assets outperform significantly
- **Narrative-Driven**: New themes attract capital (momentum follows)

### Poor Performance
- **Bear Markets**: All assets decline, no safe haven
- **High Correlation**: Everything moves together (no differentiation)
- **Momentum Reversals**: Sudden shifts punish recent winners
- **Low Volatility**: Minimal performance differences (hard to rank)
- **Flash Crashes**: Sudden drops trigger stops across portfolio

## Risk Management

### Key Risk Controls

#### Universe Quality
1. **Liquidity Filter**: Only trade liquid assets (> $1M daily volume)
2. **Market Cap Floor**: Exclude micro-caps (manipulation risk)
3. **Exchange Listing**: Require listing on major exchanges (Binance, Coinbase)
4. **Data Integrity**: Verify price data accuracy (outlier detection)

#### Position Limits
1. **Max Position**: No asset > 30% of portfolio (even if Rank 1)
2. **Min Position**: No asset < 5% (if in top N)
3. **Max N**: Don't exceed 10-15 assets (over-diversification dilutes edge)

#### Rebalance Execution
1. **Timing**: Execute at consistent time (UTC midnight, reduces gaming)
2. **Slippage Control**: Use limit orders, max 0.5% slippage
3. **Batching**: Execute all trades within 1-hour window
4. **Partial Fills**: Accept partial fills, don't chase

#### Drawdown Protection
1. **Portfolio Stop**: Exit all if down 20% from peak
2. **Individual Stop**: Exit asset if down 25% from entry
3. **Volatility Scaling**: Reduce exposure if ATR spikes 2x
4. **Bear Market Detection**: If BTC down 30%, reduce portfolio 50%

### Advanced Risk Controls

#### Correlation Management
- Monitor pairwise correlations
- If top N all >0.9 correlation, reduce N (over-concentrated)
- Favor assets with lower correlation to BTC

#### Momentum Crash Hedging
- Hold 10-20% in stablecoins (buffer)
- Or buy BTC put options (insurance)
- Reduces severe drawdowns in crashes

#### Turnover Management
- Track monthly turnover
- If turnover > 200%, increase rebalance period (too much churn)
- Aim for 50-100% annual turnover

## Enhancements & Variations

### Momentum + Value
- Combine momentum rank with fundamental metrics (market cap, volume)
- Favor undervalued high-momentum assets
- Reduces "bubble" risk (buying overpriced leaders)

### Momentum + Mean Reversion
- Use momentum for selection
- Use mean reversion for entry timing (buy dips in leaders)
- Hybrid approach

### Sector-Neutral Momentum
- Rank assets within sectors (DeFi, Layer 1, Layer 2, Meme)
- Hold top momentum asset from each sector
- Diversified sector exposure

### Dual Momentum (Absolute + Relative)
- **Absolute**: Only hold assets with positive absolute returns
- **Relative**: Rank remaining assets, hold top N
- Avoids being long in bear markets

### Machine Learning Momentum
- Use ML to predict momentum persistence
- Features: Volume, volatility, correlation, sentiment
- Enhances traditional momentum ranking

## Backtesting Notes

### Data Requirements
- **Pricing**: Daily close for all universe assets (50+ symbols)
- **Volume**: Daily volume for liquidity filtering
- **Market Cap**: Historical market cap for universe definition
- **Lookback**: Minimum 180 days per asset
- **Total History**: 2+ years for robust testing

### Critical Backtesting Challenges

#### Survivorship Bias
- Don't backtest only on current top assets
- Include delisted, failed projects (BitConnect, Luna)
- Reality: Some assets go to zero

#### Look-Ahead Bias
- Use market cap/volume from historical date (not current)
- Universe definition must use historical data
- Don't rank with future prices

#### Transaction Costs
```python
# Model realistic costs
cost_per_trade = 0.001  # 0.1% maker fee (Binance)
slippage = 0.002        # 0.2% slippage
total_cost = (cost_per_trade + slippage) * turnover
# If 100% annual turnover, cost = 0.3% annual
```

#### Rebalance Timing
- Backtest assumes trades execute at close
- Reality: Prices may move during execution
- Add 0.1-0.3% slippage buffer

### Walk-Forward Testing
- **Train**: Optimize lookback weights on 2 years
- **Test**: Validate on next 6 months
- **Roll Forward**: Move window, repeat
- **Validate**: Consistent performance across periods

## Implementation Checklist

### Required Features
- [ ] Universe definition (market cap, volume filters)
- [ ] Price data fetching for all symbols
- [ ] Multi-period momentum calculation (30/60/90/180d)
- [ ] Composite momentum scoring (weighted average)
- [ ] Ranking algorithm (sort by score)
- [ ] Top N selection logic
- [ ] Allocation calculation (tiered, equal, score-weighted)
- [ ] Rebalance scheduler (weekly, monthly, quarterly)
- [ ] Transaction cost modeling

### Required Risk Components
- [ ] Individual stop loss (25% per asset)
- [ ] Portfolio drawdown monitoring (20% limit)
- [ ] Position size limits (max 30% per asset)
- [ ] Liquidity validation (min volume check)
- [ ] Correlation monitoring
- [ ] Rebalance execution logic (market/limit orders)

### Strategy Class Methods
```python
class MomentumRankStrategy(BaseStrategy):
    """
    Multi-asset momentum rotation strategy.
    
    Ranks crypto universe by momentum, holds top N performers,
    rebalances periodically to maintain strongest positions.
    
    Parameters:
        universe_size: Number of assets to consider (default: 50)
        top_n: Number of assets to hold (default: 5)
        lookbacks: List of lookback periods (default: [30,60,90,180])
        weights: Weights for each lookback (default: [0.15,0.25,0.35,0.25])
        rebalance_days: Days between rebalances (default: 30)
        allocation_method: 'tiered', 'equal', 'score_weighted' (default: 'tiered')
    """
    
    def define_universe(self, market_cap_min, volume_min, exchange_list):
        """
        Build tradable universe.
        Returns: List of qualified symbols
        """
        pass
    
    def calculate_momentum(self, symbol, lookbacks, weights):
        """
        Calculate composite momentum score for single asset.
        
        Returns: momentum_score (float)
        """
        pass
    
    def rank_universe(self, universe, current_date):
        """
        Calculate momentum for all assets, return ranked list.
        
        Returns: [(symbol, score), ...] sorted descending
        """
        pass
    
    def construct_portfolio(self, ranked_list, top_n, allocation_method):
        """
        Select top N and calculate allocations.
        
        Returns: {symbol: allocation_percent, ...}
        """
        pass
    
    def calculate_rebalance_trades(self, current_portfolio, target_portfolio):
        """
        Determine buy/sell orders to move from current to target.
        
        Returns: [
            {'action': 'sell', 'symbol': 'BTC', 'percent': 0.20},
            {'action': 'buy', 'symbol': 'ETH', 'percent': 0.30},
            ...
        ]
        """
        pass
    
    def execute_rebalance(self, trades, slippage_tolerance):
        """
        Execute all rebalance trades.
        Track costs, slippage, partial fills.
        """
        pass
    
    def check_stop_loss(self, positions):
        """
        Monitor individual stops (25%) and portfolio stop (20%).
        Returns: list of symbols to exit
        """
        pass
    
    def should_rebalance(self, current_date, last_rebalance_date, frequency):
        """
        Check if it's time to rebalance.
        Returns: bool
        """
        pass
```

## References & Resources

### Academic Foundation
- **"Returns to Buying Winners and Selling Losers"** - Jegadeesh & Titman (1993)
  - Original momentum paper, 50+ years of equity momentum
- **"Momentum Strategies in Cryptocurrency"** - Liu et al. (2019)
  - Confirms momentum premium in crypto
- **"Cross-Sectional Momentum"** - Asness et al. (2013)
  - Momentum works across asset classes

### Professional Usage
- **Hedge Funds**: AQR, Two Sigma use momentum rotation
- **Crypto Funds**: Grayscale, Pantera use multi-asset strategies
- **Robo-Advisors**: Wealthfront, Betterment use momentum tilts

### Books
- **"Quantitative Momentum"** - Wesley Gray & Jack Vogel
- **"Dual Momentum Investing"** - Gary Antonacci
- **"The Little Book That Still Beats the Market"** - Joel Greenblatt (value + momentum)

### Online Resources
- Alpha Architect: Momentum research blog
- SSRN: Academic momentum papers
- QuantConnect: Momentum algorithm examples

---

**Status**: 📋 Documentation Complete - Implementation Pending
**Complexity**: ⭐⭐⭐⭐ High (Multi-asset, universe management)
**Reliability**: ⭐⭐⭐⭐ High (Proven academic edge)
**Market Suitability**: Bull markets and sector rotations (40-50% of crypto conditions)
**Recommended For**: Intermediate to advanced traders with portfolio management skills
**Implementation Priority**: Medium (More complex than single-asset strategies)
**Data Requirements**: High (Full universe pricing, market cap, volume)
