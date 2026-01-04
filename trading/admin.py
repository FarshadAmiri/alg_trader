"""
Django admin configuration for trading models.
"""
from django.contrib import admin
from .models import Candle, Strategy, BacktestRun, TradeResult, StrategyPerformance


@admin.register(Candle)
class CandleAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'timeframe', 'timestamp', 'close', 'volume')
    list_filter = ('symbol', 'timeframe')
    search_fields = ('symbol',)
    ordering = ('-timestamp',)


@admin.register(Strategy)
class StrategyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(BacktestRun)
class BacktestRunAdmin(admin.ModelAdmin):
    list_display = ('strategy', 'start_time', 'end_time', 'status', 'created_at')
    list_filter = ('status', 'strategy')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(TradeResult)
class TradeResultAdmin(admin.ModelAdmin):
    list_display = ('backtest', 'symbol', 'entry_time', 'direction', 'return_pct')
    list_filter = ('direction', 'symbol')
    ordering = ('-entry_time',)


@admin.register(StrategyPerformance)
class StrategyPerformanceAdmin(admin.ModelAdmin):
    list_display = ('backtest', 'total_trades', 'win_rate', 'avg_return_pct', 'max_drawdown')
    readonly_fields = ('backtest',)
