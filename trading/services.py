"""
Shared business logic for backtesting.
This module contains the core execution logic used by both CLI and web UI.
"""
import pandas as pd
import importlib
from typing import List, Dict
from django.utils import timezone
from .models import BacktestRun, TradeResult, StrategyPerformance, Candle
from core_engine.features.momentum import MomentumFeatures
from core_engine.features.volatility import VolatilityFeatures
from core_engine.features.liquidity import LiquidityFeatures, CompositeFeatures
from core_engine.backtest.engine import BacktestEngine


def execute_backtest_run(backtest: BacktestRun) -> Dict:
    """
    Execute a backtest run. Used by both CLI and web UI.
    
    Args:
        backtest: BacktestRun model instance with all parameters
        
    Returns:
        Dict with 'trades' and 'metrics' keys
        
    Raises:
        ValueError: If data not found or other execution errors
    """
    backtest.status = 'running'
    backtest.save()
    
    # Load strategy
    strategy_obj = backtest.strategy
    module_path, class_name = strategy_obj.module_path.split(':')
    module = importlib.import_module(module_path)
    strategy_class = getattr(module, class_name)
    
    # Initialize strategy with parameters
    strategy = strategy_class(parameters=strategy_obj.parameters)
    
    # Get required timeframe from strategy
    required_timeframe = strategy.preferred_timeframe
    
    # Get symbols
    symbols = backtest.symbol_universe if isinstance(backtest.symbol_universe, list) else [backtest.symbol_universe]
    
    # Load candle data using strategy's preferred timeframe
    candles_by_symbol = {}
    for symbol in symbols:
        candles_qs = Candle.objects.filter(
            symbol=symbol,
            timeframe=required_timeframe,
            timestamp__gte=backtest.start_time,
            timestamp__lte=backtest.end_time
        ).order_by('timestamp')
        
        if not candles_qs.exists():
            raise ValueError(f"No data found for {symbol} at {required_timeframe} timeframe")
        
        # Convert to DataFrame - keep timestamp as column
        df = pd.DataFrame(list(candles_qs.values('timestamp', 'open', 'high', 'low', 'close', 'volume')))
        candles_by_symbol[symbol] = df
        print(f"[DEBUG] {symbol}: {len(df)} candles from {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
    
    # Initialize features
    momentum = MomentumFeatures()
    volatility = VolatilityFeatures()
    liquidity = LiquidityFeatures()
    composite = CompositeFeatures()
    
    # Compute features for each symbol
    features_by_symbol = {}
    for symbol, candles_df in candles_by_symbol.items():
        # Compute all features (timestamp stays as column)
        features_df = momentum.compute(candles_df)
        features_df = volatility.compute(features_df)
        features_df = liquidity.compute(features_df)
        features_df = composite.compute(features_df)
        
        # Check for NaN values
        nan_cols = features_df.columns[features_df.isna().any()].tolist()
        if nan_cols:
            print(f"[DEBUG] {symbol}: Columns with NaN: {nan_cols}")
            print(f"[DEBUG] {symbol}: First non-NaN row index: {features_df.dropna().index[0] if len(features_df.dropna()) > 0 else 'ALL NaN'}")
        
        features_by_symbol[symbol] = features_df
        print(f"[DEBUG] {symbol}: {len(features_df.columns)} features computed")
    
    # Create backtest engine using strategy metadata
    engine = BacktestEngine.from_strategy(
        strategy=strategy,
        fee_bps=backtest.fee_bps,
        slippage_bps=backtest.slippage_bps,
        max_hold_override=backtest.max_hold_override if hasattr(backtest, 'max_hold_override') else None
    )
    
    # Run backtest
    print(f"[DEBUG] Running backtest from {backtest.start_time} to {backtest.end_time}")
    print(f"[DEBUG] Strategy evaluation_mode: {strategy.evaluation_mode}")
    print(f"[DEBUG] Engine window_hours: {engine.walk_forward.window_hours}, shift_hours: {engine.walk_forward.shift_hours}")
    
    results = engine.run(
        strategy=strategy,
        features_by_symbol=features_by_symbol,
        start_time=backtest.start_time,
        end_time=backtest.end_time
    )
    
    print(f"[DEBUG] Backtest complete. Results: {list(results.keys())}")
    print(f"[DEBUG] Number of trades: {len(results.get('trades_df', pd.DataFrame()))}")
    
    # Save trade results
    trades_df = results.get('trades_df', pd.DataFrame())
    if not trades_df.empty:
        for _, trade in trades_df.iterrows():
            # Convert trade to dict and serialize timestamps
            trade_dict = trade.to_dict()
            # Convert any Timestamp objects to ISO format strings
            for key, value in trade_dict.items():
                if isinstance(value, pd.Timestamp):
                    trade_dict[key] = value.isoformat()
            
            TradeResult.objects.create(
                backtest=backtest,
                symbol=trade.get('symbol', symbols[0]),
                entry_time=trade['entry_time'],
                exit_time=trade['exit_time'],
                direction=trade.get('direction', 'LONG'),
                return_pct=trade['return_pct'],
                max_drawdown=trade.get('max_drawdown', 0.0),
                metadata=trade_dict
            )
    
    # Save performance metrics
    metrics = results.get('metrics', {})
    StrategyPerformance.objects.create(
        backtest=backtest,
        total_trades=metrics.get('total_trades', 0),
        winning_trades=metrics.get('winning_trades', 0),
        losing_trades=metrics.get('losing_trades', 0),
        win_rate=metrics.get('win_rate', 0.0),
        avg_return_pct=metrics.get('avg_return_pct', 0.0),
        median_return_pct=metrics.get('median_return_pct', 0.0),
        total_return_pct=metrics.get('total_return_pct', 0.0),
        max_drawdown=metrics.get('max_drawdown', 0.0),
        profit_factor=metrics.get('profit_factor')
    )
    
    backtest.status = 'completed'
    backtest.save()
    
    return results
