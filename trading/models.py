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
    base_timeframe = models.CharField(max_length=5, default="5m")
    window_hours = models.IntegerField(default=4)
    shift_hours = models.IntegerField(default=2)
    fee_bps = models.IntegerField(
        default=10,
        help_text="Fee in basis points (10 = 0.10%)"
    )
    slippage_bps = models.IntegerField(default=0)
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
