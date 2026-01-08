"""
Portfolio evaluation metrics and comparison tools.

Evaluates portfolio-level performance and compares different combination methods.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from core_engine.strategies.base import TradingStrategy
from core_engine.portfolio.manager import PortfolioManager
from .strategy_metrics import StrategyEvaluator, StrategyMetrics


class PortfolioEvaluator:
    """Evaluate portfolio performance and compare combination methods."""
    
    def __init__(self):
        self.strategy_evaluator = StrategyEvaluator()
    
    def evaluate_portfolio(
        self,
        portfolio_returns: pd.Series,
        portfolio_trades: pd.DataFrame = None
    ) -> StrategyMetrics:
        """
        Evaluate portfolio-level performance.
        
        Args:
            portfolio_returns: Time series of portfolio returns
            portfolio_trades: Optional DataFrame with portfolio-level trades
        
        Returns:
            StrategyMetrics for the portfolio
        """
        return self.strategy_evaluator.evaluate(portfolio_returns, portfolio_trades)
    
    def compare_combinations(
        self,
        strategies: List[TradingStrategy],
        features_by_symbol: Dict[str, pd.DataFrame],
        timestamps: List,
        combination_methods: List[str] = None,
        total_capital: float = 100000.0
    ) -> pd.DataFrame:
        """
        Compare different signal combination methods.
        
        Args:
            strategies: List of TradingStrategy instances
            features_by_symbol: Historical features for backtesting
            timestamps: List of evaluation timestamps
            combination_methods: List of methods to compare (default: all)
            total_capital: Capital to allocate
        
        Returns:
            DataFrame comparing all methods with metrics
        """
        if combination_methods is None:
            combination_methods = ['weighted', 'confidence_weighted', 'rank_average', 'best_strategy']
        
        results = []
        
        for method in combination_methods:
            # Create portfolio manager with this method
            portfolio_manager = PortfolioManager(
                strategies=strategies,
                combination_method=method,
                allocation_method='proportional',
                total_capital=total_capital
            )
            
            # Simulate portfolio over time
            portfolio_values = []
            
            for timestamp in timestamps:
                try:
                    positions = portfolio_manager.get_portfolio_positions(
                        features_by_symbol,
                        timestamp
                    )
                    
                    if not positions.empty:
                        total_allocation = positions['allocation'].sum()
                        portfolio_values.append(total_allocation)
                    else:
                        portfolio_values.append(total_capital)
                
                except Exception as e:
                    portfolio_values.append(total_capital)
            
            # Calculate returns
            portfolio_series = pd.Series(portfolio_values, index=timestamps)
            returns = portfolio_series.pct_change() * 100
            returns = returns.fillna(0)
            
            # Evaluate
            metrics = self.evaluate_portfolio(returns)
            
            results.append({
                'combination_method': method,
                'sharpe_ratio': metrics.sharpe_ratio,
                'total_return': metrics.total_return,
                'max_drawdown': metrics.max_drawdown,
                'volatility': metrics.volatility,
                'calmar_ratio': metrics.calmar_ratio,
            })
        
        return pd.DataFrame(results).sort_values('sharpe_ratio', ascending=False)
    
    def calculate_strategy_contributions(
        self,
        strategies: List[TradingStrategy],
        portfolio_manager: PortfolioManager,
        features_by_symbol: Dict[str, pd.DataFrame],
        timestamp
    ) -> pd.DataFrame:
        """
        Calculate how much each strategy contributes to portfolio signals.
        
        Args:
            strategies: List of strategies
            portfolio_manager: PortfolioManager instance
            features_by_symbol: Features data
            timestamp: Evaluation time
        
        Returns:
            DataFrame with strategy contributions
        """
        all_signals = []
        
        # Collect signals from each strategy
        for strategy in strategies:
            selected_symbols = strategy.select_symbols(features_by_symbol, timestamp)
            
            for symbol in selected_symbols:
                if symbol not in features_by_symbol:
                    continue
                
                features = features_by_symbol[symbol]
                signal = strategy.generate_alpha_signal(symbol, features, timestamp)
                signal.metadata['strategy_name'] = strategy.name
                
                all_signals.append({
                    'strategy': strategy.name,
                    'symbol': symbol,
                    'alpha_score': signal.alpha_score,
                    'confidence': signal.confidence,
                })
        
        df = pd.DataFrame(all_signals)
        
        if df.empty:
            return df
        
        # Aggregate by strategy
        strategy_stats = df.groupby('strategy').agg({
            'alpha_score': ['mean', 'std', 'count'],
            'confidence': 'mean'
        }).reset_index()
        
        strategy_stats.columns = ['strategy', 'avg_alpha', 'alpha_std', 'num_signals', 'avg_confidence']
        
        return strategy_stats
    
    def calculate_diversification_score(
        self,
        allocations: Dict[str, float],
        total_capital: float
    ) -> float:
        """
        Calculate portfolio diversification score.
        
        Uses Herfindahl-Hirschman Index (HHI).
        Score of 1.0 = perfectly diversified, 0.0 = concentrated.
        
        Args:
            allocations: Dict mapping symbol -> allocation amount
            total_capital: Total capital
        
        Returns:
            Diversification score (0 to 1)
        """
        if not allocations:
            return 0.0
        
        # Calculate weights
        weights = np.array([v / total_capital for v in allocations.values()])
        
        # HHI = sum of squared weights
        hhi = np.sum(weights ** 2)
        
        # Normalize: 1/n is perfectly diversified, 1 is fully concentrated
        n = len(allocations)
        if n <= 1:
            return 0.0
        
        # Invert and normalize so higher = more diversified
        diversity_score = (1 - hhi) / (1 - 1/n)
        
        return diversity_score
    
    def compare_allocation_methods(
        self,
        combined_alphas: Dict[str, Tuple[float, float]],
        allocation_methods: List[str] = None,
        total_capital: float = 100000.0
    ) -> pd.DataFrame:
        """
        Compare different capital allocation methods.
        
        Args:
            combined_alphas: Dict mapping symbol -> (alpha, confidence)
            allocation_methods: Methods to compare
            total_capital: Capital to allocate
        
        Returns:
            DataFrame comparing allocation methods
        """
        from core_engine.portfolio.allocators import CapitalAllocator
        
        if allocation_methods is None:
            allocation_methods = ['proportional', 'equal_weight', 'top_n', 'threshold']
        
        results = []
        
        for method in allocation_methods:
            allocator = CapitalAllocator(method=method, total_capital=total_capital)
            
            # Get allocations
            allocations = allocator.allocate(combined_alphas)
            
            # Calculate metrics
            num_positions = len(allocations)
            total_allocated = sum(allocations.values())
            diversification = self.calculate_diversification_score(allocations, total_capital)
            
            # Position sizes
            if allocations:
                weights = [v / total_capital for v in allocations.values()]
                max_weight = max(weights)
                min_weight = min(weights)
                avg_weight = np.mean(weights)
            else:
                max_weight = min_weight = avg_weight = 0.0
            
            results.append({
                'allocation_method': method,
                'num_positions': num_positions,
                'total_allocated': total_allocated,
                'pct_allocated': (total_allocated / total_capital) * 100,
                'diversification_score': diversification,
                'max_position_weight': max_weight * 100,
                'min_position_weight': min_weight * 100,
                'avg_position_weight': avg_weight * 100,
            })
        
        return pd.DataFrame(results)
