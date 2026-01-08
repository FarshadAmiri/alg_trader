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
        """Initialize backtest engine (legacy interface)."""
        self.walk_forward = WalkForwardEngine(
            window_hours=window_hours,
            shift_hours=shift_hours,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps
        )
        self.metrics_calculator = PerformanceMetrics()
    
    @classmethod
    def from_strategy(
        cls,
        strategy,
        fee_bps: int = 10,
        slippage_bps: int = 0,
        max_hold_override: float = None
    ):
        """
        Create backtest engine auto-configured from strategy metadata.
        
        This is the new simplified interface - it reads the strategy's
        preferred evaluation mode and timeframe settings automatically.
        
        Args:
            strategy: TradingStrategy instance with metadata
            fee_bps: Trading fee in basis points
            slippage_bps: Slippage in basis points
            max_hold_override: Optional override for max_hold_hours
        
        Returns:
            BacktestEngine configured for the strategy
        """
        # Get strategy metadata
        max_hold = max_hold_override or getattr(strategy, 'max_hold_hours', 4.0)
        
        # Determine shift hours based on evaluation mode
        if getattr(strategy, 'evaluation_mode', 'periodic') == 'every_bar':
            # For every_bar mode, use small shift to trigger bar-by-bar
            shift_hours = 0.1
        else:
            # Use strategy's preferred evaluation interval
            shift_hours = getattr(strategy, 'evaluation_interval_hours', 2.0)
        
        return cls(
            window_hours=int(max_hold),
            shift_hours=shift_hours,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps
        )
    
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
    
    def run_portfolio_backtest(
        self,
        strategies: List,
        features_by_symbol: Dict[str, pd.DataFrame],
        start_time: datetime,
        end_time: datetime,
        combination_method: str = 'weighted',
        allocation_method: str = 'proportional',
        strategy_weights: Optional[Dict[str, float]] = None,
        total_capital: float = 100000.0
    ) -> Dict:
        """
        Run backtest for portfolio of multiple strategies (Phase 1).
        
        Args:
            strategies: List of TradingStrategy instances
            features_by_symbol: Dict of symbol -> features DataFrame
            start_time: Backtest start time
            end_time: Backtest end time
            combination_method: How to combine signals
            allocation_method: How to allocate capital
            strategy_weights: Optional strategy weights
            total_capital: Total capital to allocate
        
        Returns:
            Dictionary containing portfolio backtest results
        """
        from core_engine.portfolio.manager import PortfolioManager
        from core_engine.evaluation.portfolio_metrics import PortfolioEvaluator
        
        print(f"[PORTFOLIO ENGINE] Initializing portfolio manager...")
        print(f"[PORTFOLIO ENGINE] Strategies: {[s.name for s in strategies]}")
        print(f"[PORTFOLIO ENGINE] Combination: {combination_method}, Allocation: {allocation_method}")
        
        # Create portfolio manager
        portfolio_manager = PortfolioManager(
            strategies=strategies,
            combination_method=combination_method,
            allocation_method=allocation_method,
            strategy_weights=strategy_weights,
            total_capital=total_capital
        )
        
        print(f"[PORTFOLIO ENGINE] Portfolio manager created successfully")
        print(f"[PORTFOLIO ENGINE] Generating timestamps...")
        
        # Generate timestamps for evaluation
        timestamps = []
        current = start_time
        
        # Use the finest evaluation interval from all strategies (minimum 0.5 hours to prevent infinite loops)
        min_interval = min(
            max(0.5, getattr(s, 'evaluation_interval_hours', 2.0))  # Ensure at least 0.5 hours
            for s in strategies
        )
        
        print(f"[PORTFOLIO ENGINE] Evaluation interval: {min_interval} hours")
        
        import pandas as pd
        while current <= end_time:
            timestamps.append(current)
            current = current + pd.Timedelta(hours=min_interval)
        
        print(f"[PORTFOLIO ENGINE] Generated {len(timestamps)} timestamps from {start_time} to {end_time}")
        
        # Collect portfolio signals and allocations over time
        portfolio_history = []
        
        print(f"[PORTFOLIO ENGINE] Processing {len(timestamps)} time points...")
        processed = 0
        
        for timestamp in timestamps:
            try:
                # Progress logging every 10%
                if processed % max(1, len(timestamps) // 10) == 0:
                    progress = (processed / len(timestamps)) * 100
                    print(f"[PORTFOLIO ENGINE] Progress: {progress:.0f}% ({processed}/{len(timestamps)})")
                
                # Get portfolio positions at this timestamp
                positions = portfolio_manager.get_portfolio_positions(
                    features_by_symbol,
                    timestamp
                )
                
                if not positions.empty:
                    portfolio_history.append({
                        'timestamp': timestamp,
                        'num_positions': len(positions),
                        'total_allocation': positions['allocation'].sum(),
                        'avg_alpha': positions['alpha_score'].mean(),
                        'avg_confidence': positions['confidence'].mean(),
                        'positions': positions.to_dict('records')
                    })
                
                processed += 1
                
            except Exception as e:
                print(f"Error at {timestamp}: {e}")
                processed += 1
                continue
        
        print(f"[PORTFOLIO ENGINE] Completed processing all {processed} time points")
        
        # Convert to DataFrame
        portfolio_df = pd.DataFrame(portfolio_history)
        
        # Calculate portfolio-level metrics
        evaluator = PortfolioEvaluator()
        
        if not portfolio_df.empty:
            # Calculate returns
            portfolio_df['returns'] = portfolio_df['total_allocation'].pct_change() * 100
            portfolio_df['returns'] = portfolio_df['returns'].fillna(0)
            
            # Evaluate portfolio
            returns_series = pd.Series(
                portfolio_df['returns'].values,
                index=portfolio_df['timestamp']
            )
            portfolio_metrics = evaluator.evaluate_portfolio(returns_series)
        else:
            from core_engine.evaluation.strategy_metrics import StrategyMetrics
            portfolio_metrics = StrategyMetrics()
        
        print(f"[PORTFOLIO ENGINE] Portfolio evaluation complete")
        print(f"[PORTFOLIO ENGINE] Processed {len(portfolio_df)} time points")
        
        # Note: Individual strategy backtests are skipped for performance
        # To compare individual strategies, run them separately
        
        return {
            'portfolio_history': portfolio_df,
            'portfolio_metrics': portfolio_metrics,
            'strategy_results': {},  # Empty - run individually if needed
            'combination_method': combination_method,
            'allocation_method': allocation_method,
            'num_strategies': len(strategies),
        }
