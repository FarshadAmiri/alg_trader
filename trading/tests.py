"""
Database migration tests - Run this to verify migrations work correctly.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import datetime, timedelta
from trading.models import (
    Candle, Strategy, BacktestRun, TradeResult, StrategyPerformance
)


class ModelTests(TestCase):
    """Test database models."""
    
    def setUp(self):
        """Set up test data."""
        self.strategy = Strategy.objects.create(
            name="Test Strategy",
            module_path="core_engine.strategies.macd_rsi_confluence:MACDRSIStrategy",
            description="Test strategy for unit tests",
            parameters={'test': True},
            is_active=True
        )
    
    def test_candle_creation(self):
        """Test creating candle records."""
        candle = Candle.objects.create(
            symbol='BTC/USDT',
            timeframe='5m',
            timestamp=timezone.now(),
            open=50000.0,
            high=50100.0,
            low=49900.0,
            close=50050.0,
            volume=100.5
        )
        
        self.assertEqual(candle.symbol, 'BTC/USDT')
        self.assertGreater(candle.close, candle.low)
        self.assertLess(candle.close, candle.high)
    
    def test_strategy_creation(self):
        """Test strategy model."""
        self.assertTrue(self.strategy.is_active)
        self.assertEqual(self.strategy.parameters, {'test': True})
    
    def test_backtest_run_creation(self):
        """Test backtest run model."""
        now = timezone.now()
        backtest = BacktestRun.objects.create(
            strategy=self.strategy,
            symbol_universe=['BTC/USDT', 'ETH/USDT'],
            start_time=now - timedelta(days=7),
            end_time=now,
            window_hours=4,
            shift_hours=2,
            fee_bps=10
        )
        
        self.assertEqual(backtest.status, 'pending')
        self.assertEqual(len(backtest.symbol_universe), 2)
    
    def test_trade_result_creation(self):
        """Test trade result model."""
        now = timezone.now()
        backtest = BacktestRun.objects.create(
            strategy=self.strategy,
            symbol_universe=['BTC/USDT'],
            start_time=now - timedelta(days=7),
            end_time=now
        )
        
        trade = TradeResult.objects.create(
            backtest=backtest,
            symbol='BTC/USDT',
            entry_time=now - timedelta(hours=4),
            exit_time=now,
            direction='LONG',
            return_pct=2.5,
            max_drawdown=0.5
        )
        
        self.assertEqual(trade.direction, 'LONG')
        self.assertGreater(trade.return_pct, 0)
    
    def test_performance_creation(self):
        """Test strategy performance model."""
        now = timezone.now()
        backtest = BacktestRun.objects.create(
            strategy=self.strategy,
            symbol_universe=['BTC/USDT'],
            start_time=now - timedelta(days=7),
            end_time=now
        )
        
        perf = StrategyPerformance.objects.create(
            backtest=backtest,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=60.0,
            avg_return_pct=1.5,
            median_return_pct=1.2,
            max_drawdown=2.0,
            total_return_pct=15.0
        )
        
        self.assertEqual(perf.total_trades, 10)
        self.assertEqual(perf.win_rate, 60.0)


class CoreEngineTests(TestCase):
    """Test core engine components (no Django dependencies)."""
    
    def test_feature_computation(self):
        """Test feature computation."""
        import pandas as pd
        from core_engine.features.momentum import MomentumFeatures
        
        # Create sample data
        dates = pd.date_range('2025-01-01', periods=100, freq='1h')
        df = pd.DataFrame({
            'timestamp': dates,
            'open': 50000.0,
            'high': 50100.0,
            'low': 49900.0,
            'close': 50050.0,
            'volume': 100.0
        })
        
        # Compute features
        momentum = MomentumFeatures()
        result = momentum.compute(df)
        
        # Check features exist
        self.assertIn('rsi', result.columns)
        self.assertIn('macd_histogram', result.columns)
    
    def test_strategy_interface(self):
        """Test strategy interface."""
        from core_engine.strategies.macd_rsi_confluence import MACDRSIStrategy
        
        strategy = MACDRSIStrategy()
        self.assertEqual(strategy.name, 'macd_rsi_confluence')
        self.assertIn('rsi_min', strategy.parameters)
