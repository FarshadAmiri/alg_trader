"""
Main backtesting engine orchestrator.
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from .walkforward import WalkForwardEngine, TradeResult
from .metrics import PerformanceMetrics


class BacktestEngine:
    """
    Main backtesting engine that coordinates all components.
    """
    
    def __init__(
        self,
        window_hours: int = 4,
        shift_hours: int = 2,
        fee_bps: int = 10,
        slippage_bps: int = 0
    ):
        """Initialize backtest engine."""
        self.walk_forward = WalkForwardEngine(
            window_hours=window_hours,
            shift_hours=shift_hours,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps
        )
        self.metrics_calculator = PerformanceMetrics()
    
    def run(
        self,
        strategy,
        features_by_symbol: Dict[str, pd.DataFrame],
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """
        Run complete backtest and return results.
        
        Args:
            strategy: TradingStrategy instance
            features_by_symbol: Dict of symbol -> features DataFrame
            start_time: Backtest start time
            end_time: Backtest end time
        
        Returns:
            Dictionary containing:
                - trades: List of TradeResult objects
                - metrics: Performance metrics dictionary
                - trades_df: DataFrame of trades
        """
        # Run walk-forward backtest
        trade_results = self.walk_forward.run_backtest(
            strategy,
            features_by_symbol,
            start_time,
            end_time
        )
        
        # Convert to DataFrame
        trades_df = self._results_to_dataframe(trade_results)
        
        # Calculate metrics
        metrics = self.metrics_calculator.calculate_metrics(trades_df)
        
        return {
            'trades': trade_results,
            'trades_df': trades_df,
            'metrics': metrics,
        }
    
    def _results_to_dataframe(self, results: List[TradeResult]) -> pd.DataFrame:
        """Convert trade results to DataFrame."""
        if not results:
            return pd.DataFrame(columns=[
                'symbol', 'entry_time', 'exit_time', 'direction',
                'return_pct', 'max_drawdown'
            ])
        
        data = []
        for result in results:
            data.append({
                'symbol': result.symbol,
                'entry_time': result.entry_time,
                'exit_time': result.exit_time,
                'direction': result.direction,
                'return_pct': result.return_pct,
                'max_drawdown': result.max_drawdown,
            })
        
        return pd.DataFrame(data)
