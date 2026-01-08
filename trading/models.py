"""
Django models for trading app.
NO trading logic here - only persistence.
"""
from django.db import models


class Candle(models.Model):
    """Base timeframe OHLCV data storage."""
    symbol = models.CharField(max_length=20)
    timeframe = models.CharField(max_length=5)  # "5m", "1h", etc.
    timestamp = models.DateTimeField()
    open = models.FloatField()
    high = models.FloatField()
    low = models.FloatField()
    close = models.FloatField()
    volume = models.FloatField()

    class Meta:
        unique_together = ("symbol", "timeframe", "timestamp")
        indexes = [
            models.Index(fields=["symbol", "timeframe", "timestamp"]),
            models.Index(fields=["timestamp"]),
        ]
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.symbol} {self.timeframe} @ {self.timestamp}"


class Strategy(models.Model):
    """Strategy metadata registry."""
    name = models.CharField(max_length=100, unique=True)
    module_path = models.CharField(
        max_length=200,
        help_text="e.g. core_engine.strategies.macd_rsi_confluence:MACDRSIStrategy"
    )
    description = models.TextField(blank=True)
    parameters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Strategy hyperparameters as JSON"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Strategies"
        ordering = ['name']

    def __str__(self):
        return self.name


class BacktestRun(models.Model):
    """Experiment definition for a backtest."""
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    symbol_universe = models.JSONField(help_text="List of symbols to evaluate")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # Auto-populated from strategy metadata (kept for database records)
    base_timeframe = models.CharField(
        max_length=5, 
        default="5m",
        help_text="Auto-populated from strategy.preferred_timeframe"
    )
    window_hours = models.FloatField(
        default=4,
        help_text="Auto-populated from strategy.max_hold_hours"
    )
    shift_hours = models.FloatField(
        default=2,
        help_text="Auto-populated from strategy.evaluation_interval_hours"
    )
    
    # User-configurable parameters
    max_hold_override = models.FloatField(
        null=True,
        blank=True,
        help_text="Optional: Override strategy's default max hold time (hours)"
    )
    fee_bps = models.IntegerField(
        default=10,
        help_text="Fee in basis points (10 = 0.10%)"
    )
    slippage_bps = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        default='pending',
        choices=[
            ('pending', 'Pending'),
            ('running', 'Running'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ]
    )
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.strategy.name} - {self.start_time.date()} to {self.end_time.date()}"


class TradeResult(models.Model):
    """Individual trade outcome from a backtest window."""
    backtest = models.ForeignKey(BacktestRun, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=20)
    entry_time = models.DateTimeField()
    exit_time = models.DateTimeField()
    direction = models.CharField(max_length=10, default="LONG")
    return_pct = models.FloatField(help_text="Return % after fees/slippage")
    max_drawdown = models.FloatField(help_text="Max drawdown during holding period")
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional: feature snapshots, ranks, etc."
    )

    class Meta:
        ordering = ['entry_time']
        indexes = [
            models.Index(fields=['backtest', 'entry_time']),
        ]

    def __str__(self):
        return f"{self.symbol} {self.direction} @ {self.entry_time} -> {self.return_pct:.2f}%"


class StrategyPerformance(models.Model):
    """Aggregated performance metrics for a backtest."""
    backtest = models.OneToOneField(BacktestRun, on_delete=models.CASCADE)
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.FloatField(default=0.0)
    avg_return_pct = models.FloatField(default=0.0)
    median_return_pct = models.FloatField(default=0.0)
    profit_factor = models.FloatField(null=True, blank=True)
    max_drawdown = models.FloatField(default=0.0)
    total_return_pct = models.FloatField(default=0.0)
    
    class Meta:
        verbose_name_plural = "Strategy performances"

    def __str__(self):
        return f"Performance: {self.backtest}"


# ============================================================================
# Phase 1: Alpha Signal Architecture Models
# ============================================================================

class StrategySignalRecord(models.Model):
    """Store individual strategy alpha signals (Phase 1)."""
    strategy_name = models.CharField(max_length=100, db_index=True)
    symbol = models.CharField(max_length=20, db_index=True)
    timestamp = models.DateTimeField(db_index=True)
    
    # Alpha signal components
    alpha_score = models.FloatField(
        help_text="Alpha score from -1 (strong sell) to +1 (strong buy)"
    )
    confidence = models.FloatField(
        help_text="Confidence level from 0 to 1"
    )
    horizon_days = models.IntegerField(
        help_text="Prediction timeframe in days"
    )
    volatility_adjusted = models.BooleanField(
        default=False,
        help_text="Whether alpha_score accounts for volatility"
    )
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Strategy-specific details (indicators, thresholds, etc.)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['strategy_name', 'symbol', 'timestamp']),
            models.Index(fields=['timestamp', 'symbol']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.strategy_name} - {self.symbol} @ {self.timestamp}: {self.alpha_score:.3f}"


class PortfolioAllocation(models.Model):
    """Track portfolio allocation decisions (Phase 1)."""
    timestamp = models.DateTimeField(db_index=True)
    
    # Configuration
    combination_method = models.CharField(
        max_length=50,
        help_text="Signal combination method used"
    )
    allocation_method = models.CharField(
        max_length=50,
        help_text="Capital allocation method used"
    )
    total_capital = models.FloatField(help_text="Total capital allocated")
    
    # Allocations (dict mapping symbol -> dollar amount)
    allocations = models.JSONField(
        help_text="Dict mapping symbol -> allocation amount"
    )
    
    # Combined alpha scores (dict mapping symbol -> (alpha, confidence))
    combined_alphas = models.JSONField(
        blank=True,
        default=dict,
        help_text="Combined alpha scores for each symbol"
    )
    
    # Constraints applied
    constraints = models.JSONField(
        blank=True,
        default=dict,
        help_text="Constraints used (max_position_pct, etc.)"
    )
    
    # Metadata
    num_positions = models.IntegerField(default=0)
    num_strategies = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"Portfolio @ {self.timestamp}: {self.num_positions} positions"


class StrategyEvaluation(models.Model):
    """Track detailed performance metrics for strategies (Phase 1)."""
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    evaluation_date = models.DateField(db_index=True)
    lookback_days = models.IntegerField(
        help_text="Number of days used for evaluation"
    )
    
    # Return metrics
    total_return = models.FloatField(default=0.0)
    cagr = models.FloatField(
        default=0.0,
        help_text="Compound Annual Growth Rate"
    )
    
    # Risk-adjusted returns
    sharpe_ratio = models.FloatField(default=0.0)
    sortino_ratio = models.FloatField(default=0.0, null=True, blank=True)
    calmar_ratio = models.FloatField(default=0.0, null=True, blank=True)
    
    # Risk metrics
    max_drawdown = models.FloatField(default=0.0)
    volatility = models.FloatField(default=0.0)
    var_95 = models.FloatField(
        default=0.0,
        null=True,
        blank=True,
        help_text="Value at Risk (95% confidence)"
    )
    
    # Trading metrics
    win_rate = models.FloatField(default=0.0)
    profit_factor = models.FloatField(default=0.0, null=True, blank=True)
    avg_win_loss_ratio = models.FloatField(default=0.0, null=True, blank=True)
    
    # Efficiency metrics
    turnover = models.FloatField(
        default=0.0,
        null=True,
        blank=True,
        help_text="Portfolio turnover rate"
    )
    avg_holding_period = models.FloatField(
        default=0.0,
        null=True,
        blank=True,
        help_text="Average holding period in hours"
    )
    
    # Alpha metrics
    ic_mean = models.FloatField(
        default=0.0,
        null=True,
        blank=True,
        help_text="Mean Information Coefficient (alpha vs actual correlation)"
    )
    alpha_decay = models.FloatField(
        default=0.0,
        null=True,
        blank=True,
        help_text="How quickly predictive power fades"
    )
    
    # All metrics as JSON (for extensibility)
    metrics_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Complete metrics dictionary"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('strategy', 'evaluation_date', 'lookback_days')
        ordering = ['-evaluation_date']
        indexes = [
            models.Index(fields=['strategy', 'evaluation_date']),
        ]
    
    def __str__(self):
        return f"{self.strategy.name} eval on {self.evaluation_date} (Sharpe: {self.sharpe_ratio:.2f})"

