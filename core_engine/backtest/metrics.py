"""
Performance metrics computation.
"""
import pandas as pd
import numpy as np
from typing import List, Dict


class PerformanceMetrics:
    """Calculate performance metrics from trade results."""
    
    @staticmethod
    def calculate_metrics(trades: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive performance metrics.
        
        Args:
            trades: DataFrame with columns [return_pct, max_drawdown, ...]
        
        Returns:
            Dictionary of metrics
        """
        if trades.empty:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_return_pct': 0.0,
                'median_return_pct': 0.0,
                'total_return_pct': 0.0,
                'max_drawdown': 0.0,
                'profit_factor': None,
                'sharpe_ratio': None,
            }
        
        returns = trades['return_pct']
        
        total_trades = len(trades)
        winning_trades = len(trades[trades['return_pct'] > 0])
        losing_trades = len(trades[trades['return_pct'] <= 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        avg_return = returns.mean()
        median_return = returns.median()
        total_return = returns.sum()  # Simple sum (no compounding in v1)
        
        # Max drawdown
        max_dd = trades['max_drawdown'].max() if 'max_drawdown' in trades.columns else 0.0
        
        # Profit factor
        gross_profit = trades[trades['return_pct'] > 0]['return_pct'].sum()
        gross_loss = abs(trades[trades['return_pct'] < 0]['return_pct'].sum())
        
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None
        
        # Sharpe ratio (assuming trades are independent samples)
        sharpe = (avg_return / returns.std()) if returns.std() > 0 else None
        
        metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_return_pct': avg_return,
            'median_return_pct': median_return,
            'total_return_pct': total_return,
            'max_drawdown': max_dd,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe,
        }
        
        return metrics
    
    @staticmethod
    def calculate_rolling_metrics(
        trades: pd.DataFrame,
        window: int = 20
    ) -> pd.DataFrame:
        """
        Calculate rolling performance metrics.
        
        Args:
            trades: DataFrame with trade results
            window: Rolling window size
        
        Returns:
            DataFrame with rolling metrics
        """
        if trades.empty or len(trades) < window:
            return pd.DataFrame()
        
        trades = trades.sort_values('entry_time').reset_index(drop=True)
        
        rolling_win_rate = []
        rolling_avg_return = []
        
        for i in range(len(trades) - window + 1):
            window_trades = trades.iloc[i:i + window]
            
            wins = len(window_trades[window_trades['return_pct'] > 0])
            win_rate = wins / window * 100
            
            avg_return = window_trades['return_pct'].mean()
            
            rolling_win_rate.append(win_rate)
            rolling_avg_return.append(avg_return)
        
        result = pd.DataFrame({
            'window_start': range(len(rolling_win_rate)),
            'rolling_win_rate': rolling_win_rate,
            'rolling_avg_return': rolling_avg_return,
        })
        
        return result
