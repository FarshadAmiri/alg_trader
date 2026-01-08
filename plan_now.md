# Implementation Plan - Phase 1 (Today)

## Executive Summary
Transform the current binary signal system into a professional alpha-score architecture with portfolio management capabilities. This foundation will support future LLM-driven evolution.

---

## 1. Strategy Layer Refactoring

### 1.1 Update Base Strategy Interface

**File**: `core_engine/strategies/base.py`

**Current State**: Strategies return simple signals
**Target State**: Strategies return rich alpha signals

```python
@dataclass
class StrategySignal:
    """Standardized output from all strategies"""
    timestamp: datetime
    symbol: str
    alpha_score: float        # -1 (strong sell) to +1 (strong buy), 0 = neutral
    confidence: float         # 0 to 1, how certain the strategy is
    horizon_days: int         # prediction timeframe (1, 5, 20, etc.)
    volatility_adjusted: bool # whether alpha_score already accounts for volatility
    metadata: Dict[str, Any]  # strategy-specific details (indicators, thresholds, etc.)
```

**Key Changes**:
- Add `generate_alpha_signal()` method (replaces or complements existing signal generation)
- Keep backward compatibility with existing `generate_signals()` for now
- Add normalization utilities for alpha scores (z-score, min-max, etc.)

### 1.2 Refactor Existing Strategies

Update these strategies to use new interface:
1. `bollinger_mean_reversion.py`
2. `macd_rsi_confluence.py`
3. `momentum_rank.py`

**Example transformation**:
```python
# Old way
def generate_signals(self, data):
    if RSI < 30:
        return 'BUY'
    elif RSI > 70:
        return 'SELL'

# New way
def generate_alpha_signal(self, data):
    rsi = calculate_rsi(data)
    
    # Convert RSI to alpha score (-1 to 1)
    if rsi < 30:
        alpha_score = (30 - rsi) / 30  # 0 to 1 range
    elif rsi > 70:
        alpha_score = (70 - rsi) / 30  # -1 to 0 range
    else:
        alpha_score = 0
    
    # Confidence based on distance from threshold
    confidence = abs(alpha_score)
    
    return StrategySignal(
        timestamp=data.index[-1],
        symbol=self.symbol,
        alpha_score=alpha_score,
        confidence=confidence,
        horizon_days=self.params.get('horizon', 5),
        volatility_adjusted=False,
        metadata={'rsi': rsi, 'threshold_upper': 70, 'threshold_lower': 30}
    )
```

---

## 2. Portfolio Manager (Asset Manager)

### 2.1 Create Portfolio Manager Module

**File**: `core_engine/portfolio/manager.py`

**Responsibilities**:
- Combine signals from multiple strategies
- Rank assets based on combined alpha scores
- Allocate capital across positions
- Handle conflicts between strategies
- Apply portfolio constraints

```python
class PortfolioManager:
    """Combines strategy signals and manages asset allocation"""
    
    def __init__(self, strategies: List[Strategy], combination_method: str = 'weighted'):
        self.strategies = strategies
        self.combination_method = combination_method
        self.strategy_weights = {}  # strategy_name -> weight
    
    def combine_signals(self, signals: List[StrategySignal]) -> Dict[str, float]:
        """
        Combine multiple strategy signals into single alpha per asset
        
        Methods:
        - 'weighted': weighted average of alpha scores
        - 'rank_average': average of strategy ranks
        - 'confidence_weighted': weight by confidence levels
        """
        pass
    
    def allocate_capital(self, combined_alphas: Dict[str, float], 
                        total_capital: float) -> Dict[str, float]:
        """
        Allocate capital to assets based on combined alpha scores
        
        Returns: {symbol: target_position_value}
        """
        pass
    
    def apply_constraints(self, allocations: Dict[str, float]) -> Dict[str, float]:
        """
        Apply risk constraints:
        - Max position size (% of portfolio)
        - Max sector exposure
        - Min number of positions (diversification)
        """
        pass
```

### 2.2 Signal Combination Methods

Implement these combination methods (user-selectable):

1. **Weighted Average** (default)
   - `combined_alpha = Σ(weight_i × alpha_i)`
   
2. **Confidence-Weighted Average**
   - `combined_alpha = Σ(confidence_i × alpha_i) / Σ(confidence_i)`
   
3. **Rank-Based**
   - Rank assets by each strategy, average ranks
   - More robust to outliers

4. **Best Strategy** (fallback)
   - Use signal from highest-confidence strategy

### 2.3 Capital Allocation Methods

1. **Proportional to Alpha** (simple)
   - Higher alpha = larger position
   
2. **Kelly Criterion** (optimal)
   - Position size based on edge and odds
   - Requires win rate estimation
   
3. **Risk Parity**
   - Equal risk contribution from each position
   - Volatility-adjusted sizing

---

## 3. Enhanced Evaluation Framework

### 3.1 Strategy Evaluation Module

**File**: `core_engine/evaluation/strategy_metrics.py`

**Metrics to Calculate**:

```python
class StrategyEvaluator:
    """Comprehensive strategy evaluation"""
    
    def evaluate(self, strategy_results: pd.DataFrame) -> StrategyMetrics:
        """
        Calculate full suite of metrics for a strategy
        """
        return StrategyMetrics(
            # Returns
            total_return=self._total_return(results),
            cagr=self._cagr(results),
            
            # Risk-adjusted returns
            sharpe_ratio=self._sharpe(results),
            sortino_ratio=self._sortino(results),
            calmar_ratio=self._calmar(results),
            
            # Risk metrics
            max_drawdown=self._max_drawdown(results),
            volatility=self._volatility(results),
            var_95=self._value_at_risk(results, 0.95),
            
            # Trading metrics
            win_rate=self._win_rate(results),
            profit_factor=self._profit_factor(results),
            avg_win_loss_ratio=self._avg_win_loss_ratio(results),
            
            # Efficiency
            turnover=self._turnover(results),
            avg_holding_period=self._avg_holding_period(results),
            
            # Alpha metrics
            alpha_decay=self._alpha_decay(results),  # how quickly predictive power fades
            ic_mean=self._information_coefficient(results),  # alpha vs actual return correlation
        )
```

### 3.2 Portfolio Evaluator

**File**: `core_engine/evaluation/portfolio_metrics.py`

```python
class PortfolioEvaluator:
    """Evaluate combined portfolio performance"""
    
    def compare_combinations(self, strategies: List[Strategy], 
                           methods: List[str]) -> pd.DataFrame:
        """
        Test different signal combination methods
        Returns comparison table of all metrics
        """
        pass
```

---

## 4. Database Schema Updates

### 4.1 New Models

**File**: `trading/models.py`

```python
class StrategySignal(models.Model):
    """Store individual strategy signals"""
    strategy_name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    timestamp = models.DateTimeField()
    alpha_score = models.FloatField()
    confidence = models.FloatField()
    horizon_days = models.IntegerField()
    volatility_adjusted = models.BooleanField()
    metadata = models.JSONField()
    
class PortfolioAllocation(models.Model):
    """Track portfolio allocation decisions"""
    timestamp = models.DateTimeField()
    combination_method = models.CharField(max_length=50)
    allocations = models.JSONField()  # {symbol: weight}
    total_capital = models.FloatField()
    
class StrategyPerformance(models.Model):
    """Track performance metrics over time"""
    strategy_name = models.CharField(max_length=100)
    evaluation_date = models.DateField()
    lookback_days = models.IntegerField()
    sharpe_ratio = models.FloatField()
    total_return = models.FloatField()
    max_drawdown = models.FloatField()
    win_rate = models.FloatField()
    ic_mean = models.FloatField()  # Information coefficient
    metrics_json = models.JSONField()  # all other metrics
```

---

## 5. Backtesting Engine Updates

### 5.1 Enhanced Backtest Runner

**File**: `core_engine/backtest/engine.py`

**Updates**:
1. Support portfolio-level backtesting (not just single strategy)
2. Test different signal combination methods
3. Calculate portfolio-level metrics
4. Generate signal distribution analysis

```python
class PortfolioBacktest:
    """Backtest entire portfolio with multiple strategies"""
    
    def run(self, strategies: List[Strategy], 
            combination_method: str,
            start_date: date,
            end_date: date) -> BacktestResult:
        """
        Run backtest with portfolio management layer
        """
        pass
```

---

## 6. UI Updates

### 6.1 Strategy Display Enhancements

**Template**: `trading/templates/trading/strategy_list.html`

**Show for each strategy**:
- Current alpha score distribution (histogram)
- Confidence levels over time
- Key performance metrics
- Info modal with strategy README

### 6.2 New Portfolio Manager View

**Template**: `trading/templates/trading/portfolio_manager.html`

**Features**:
- Select active strategies
- Set strategy weights
- Choose combination method
- View current allocations
- Compare combination methods performance

### 6.3 Enhanced Backtest Results

**Template**: `trading/templates/trading/backtest_results.html`

**Additional visualizations**:
- Alpha score vs actual returns scatter plot
- Signal strength distribution
- Portfolio allocation over time
- Strategy contribution breakdown

---

## 7. Implementation Order (Today)

### Phase 1: Core Infrastructure (2-3 hours)
1. ✅ Create `StrategySignal` dataclass in `base.py`
2. ✅ Add `generate_alpha_signal()` to base Strategy class
3. ✅ Create `core_engine/portfolio/` directory
4. ✅ Implement `PortfolioManager` class
5. ✅ Create database migrations for new models

### Phase 2: Strategy Refactoring (2-3 hours)
6. ✅ Refactor `bollinger_mean_reversion.py` to new interface
7. ✅ Refactor `macd_rsi_confluence.py` to new interface
8. ✅ Refactor `momentum_rank.py` to new interface
9. ✅ Add alpha score normalization utilities

### Phase 3: Evaluation Framework (2 hours)
10. ✅ Create `core_engine/evaluation/` directory
11. ✅ Implement `StrategyEvaluator` class
12. ✅ Implement `PortfolioEvaluator` class
13. ✅ Add comparison methods

### Phase 4: Backtesting Integration (1-2 hours)
14. ✅ Update backtest engine for portfolio mode
15. ✅ Add signal combination testing
16. ✅ Update metrics calculation

### Phase 5: UI Updates (2-3 hours)
17. ✅ Add portfolio manager view
18. ✅ Update strategy display with alpha scores
19. ✅ Enhanced backtest results visualization
20. ✅ Add combination method comparison table

### Phase 6: Testing & Documentation (1 hour)
21. ✅ Test all refactored strategies
22. ✅ Test portfolio combinations
23. ✅ Update README with new architecture
24. ✅ Create usage examples

---

## 8. Success Criteria

By end of today, we should have:

- ✅ All existing strategies output alpha scores + confidence
- ✅ Portfolio manager that combines multiple strategy signals
- ✅ At least 3 signal combination methods working
- ✅ Enhanced evaluation metrics for strategies and portfolios
- ✅ UI to configure and test portfolio combinations
- ✅ Backtests that show portfolio vs individual strategy performance
- ✅ Database models to track signals and allocations
- ✅ Clear, extensible architecture for future LLM evolution

---

## 9. Key Design Principles

### Backward Compatibility
- Keep existing signal generation working during transition
- Gradual migration path

### Extensibility
- Easy to add new strategies
- Easy to add new combination methods
- Easy to add new evaluation metrics

### Modularity
- Strategy layer independent from portfolio layer
- Portfolio layer independent from execution layer
- Clear interfaces between layers

### Data-Driven
- All signals stored in database
- All decisions auditable
- Easy to analyze historical performance

---

## 10. File Structure After Implementation

```
core_engine/
├── strategies/
│   ├── base.py              # ✨ Updated with StrategySignal
│   ├── bollinger_mean_reversion.py  # ✨ Refactored
│   ├── macd_rsi_confluence.py       # ✨ Refactored
│   └── momentum_rank.py             # ✨ Refactored
├── portfolio/               # 🆕 New module
│   ├── __init__.py
│   ├── manager.py          # 🆕 PortfolioManager
│   ├── combiners.py        # 🆕 Signal combination methods
│   └── allocators.py       # 🆕 Capital allocation methods
├── evaluation/             # 🆕 New module
│   ├── __init__.py
│   ├── strategy_metrics.py # 🆕 Strategy evaluator
│   └── portfolio_metrics.py # 🆕 Portfolio evaluator
└── backtest/
    └── engine.py           # ✨ Updated for portfolio backtesting

trading/
├── models.py               # ✨ New models added
├── views.py                # ✨ Portfolio manager views
└── templates/
    └── trading/
        ├── portfolio_manager.html    # 🆕 New template
        ├── strategy_list.html        # ✨ Updated
        └── backtest_results.html     # ✨ Enhanced
```

---

## Notes

- This plan focuses on solid foundations
- Every component designed to be LLM-friendly (for future evolution)
- Maintains clean separation of concerns
- Professional-grade architecture matching industry standards
- All changes testable and measurable
