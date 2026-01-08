"""
Strategy evaluation metrics and analysis.

Calculates comprehensive performance metrics for trading strategies.
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class StrategyMetrics:
    """Complete set of strategy performance metrics."""
    
    # Returns
    total_return: float = 0.0
    cagr: float = 0.0
    
    # Risk-adjusted returns
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Risk metrics
    max_drawdown: float = 0.0
    volatility: float = 0.0
    var_95: float = 0.0  # Value at Risk (95%)
    
    # Trading metrics
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win_loss_ratio: float = 0.0
    
    # Efficiency
    turnover: float = 0.0
    avg_holding_period: float = 0.0  # hours
    
    # Alpha metrics
    ic_mean: float = 0.0  # Information coefficient
    alpha_decay: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def __str__(self) -> str:
        return (f"Sharpe: {self.sharpe_ratio:.2f}, "
                f"Return: {self.total_return:.2f}%, "
                f"MaxDD: {self.max_drawdown:.2f}%, "
                f"WinRate: {self.win_rate:.1f}%")


class StrategyEvaluator:
    """Comprehensive strategy evaluation and metrics calculation."""
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize evaluator.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculation (default 2%)
        """
        self.risk_free_rate = risk_free_rate
    
    def evaluate(self, returns: pd.Series, trades: Optional[pd.DataFrame] = None) -> StrategyMetrics:
        """
        Calculate complete strategy metrics.
        
        Args:
            returns: Time series of strategy returns (percentage)
            trades: Optional DataFrame with trade details (entry_time, exit_time, return_pct)
        
        Returns:
            StrategyMetrics with all calculated metrics
        """
        metrics = StrategyMetrics()
        
        if returns.empty:
            return metrics
        
        # Return metrics
        metrics.total_return = self._total_return(returns)
        metrics.cagr = self._cagr(returns)
        
        # Risk-adjusted returns
        metrics.sharpe_ratio = self._sharpe_ratio(returns)
        metrics.sortino_ratio = self._sortino_ratio(returns)
        metrics.calmar_ratio = self._calmar_ratio(returns)
        
        # Risk metrics
        metrics.max_drawdown = self._max_drawdown(returns)
        metrics.volatility = self._volatility(returns)
        metrics.var_95 = self._value_at_risk(returns, 0.95)
        
        # Trading metrics (if trades provided)
        if trades is not None and not trades.empty:
            metrics.total_trades = len(trades)
            metrics.win_rate = self._win_rate(trades)
            metrics.profit_factor = self._profit_factor(trades)
            metrics.avg_win_loss_ratio = self._avg_win_loss_ratio(trades)
            
            if 'entry_time' in trades.columns and 'exit_time' in trades.columns:
                metrics.avg_holding_period = self._avg_holding_period(trades)
        
        return metrics
    
    def _total_return(self, returns: pd.Series) -> float:
        """Calculate total return percentage."""
        cumulative = (1 + returns / 100).cumprod()
        return (cumulative.iloc[-1] - 1) * 100
    
    def _cagr(self, returns: pd.Series) -> float:
        """Calculate Compound Annual Growth Rate."""
        if len(returns) < 2:
            return 0.0
        
        total_return = self._total_return(returns)
        
        # Estimate number of years (assuming daily or more frequent data)
        if hasattr(returns.index, 'to_pydatetime'):
            start = returns.index[0]
            end = returns.index[-1]
            years = (end - start).days / 365.25
        else:
            # Fallback: assume each observation is 1 day
            years = len(returns) / 252  # 252 trading days
        
        if years <= 0:
            return 0.0
        
        cagr = (np.power(1 + total_return / 100, 1 / years) - 1) * 100
        return cagr
    
    def _sharpe_ratio(self, returns: pd.Series) -> float:
        """
        Calculate Sharpe ratio.
        
        Annualized Sharpe = (mean_return - risk_free) / std_return * sqrt(periods_per_year)
        """
        if returns.std() == 0:
            return 0.0
        
        # Annualize based on frequency (assume daily data, ~252 trading days)
        periods_per_year = 252
        
        excess_return = returns.mean() - (self.risk_free_rate * 100 / periods_per_year)
        sharpe = (excess_return / returns.std()) * np.sqrt(periods_per_year)
        
        return sharpe
    
    def _sortino_ratio(self, returns: pd.Series) -> float:
        """
        Calculate Sortino ratio (like Sharpe but only penalizes downside volatility).
        """
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        
        periods_per_year = 252
        excess_return = returns.mean() - (self.risk_free_rate * 100 / periods_per_year)
        
        sortino = (excess_return / downside_returns.std()) * np.sqrt(periods_per_year)
        
        return sortino
    
    def _calmar_ratio(self, returns: pd.Series) -> float:
        """Calculate Calmar ratio (CAGR / Max Drawdown)."""
        cagr = self._cagr(returns)
        max_dd = abs(self._max_drawdown(returns))
        
        if max_dd == 0:
            return 0.0
        
        return cagr / max_dd
    
    def _max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown percentage."""
        cumulative = (1 + returns / 100).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max * 100
        
        return drawdown.min()
    
    def _volatility(self, returns: pd.Series) -> float:
        """Calculate annualized volatility."""
        periods_per_year = 252
        return returns.std() * np.sqrt(periods_per_year)
    
    def _value_at_risk(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """Calculate Value at Risk at given confidence level."""
        return np.percentile(returns, (1 - confidence) * 100)
    
    def _win_rate(self, trades: pd.DataFrame) -> float:
        """Calculate win rate percentage."""
        if 'return_pct' not in trades.columns:
            return 0.0
        
        winning_trades = (trades['return_pct'] > 0).sum()
        total_trades = len(trades)
        
        if total_trades == 0:
            return 0.0
        
        return (winning_trades / total_trades) * 100
    
    def _profit_factor(self, trades: pd.DataFrame) -> float:
        """Calculate profit factor (total wins / total losses)."""
        if 'return_pct' not in trades.columns:
            return 0.0
        
        wins = trades[trades['return_pct'] > 0]['return_pct'].sum()
        losses = abs(trades[trades['return_pct'] < 0]['return_pct'].sum())
        
        if losses == 0:
            return 0.0 if wins == 0 else float('inf')
        
        return wins / losses
    
    def _avg_win_loss_ratio(self, trades: pd.DataFrame) -> float:
        """Calculate average win / average loss ratio."""
        if 'return_pct' not in trades.columns:
            return 0.0
        
        wins = trades[trades['return_pct'] > 0]['return_pct']
        losses = trades[trades['return_pct'] < 0]['return_pct']
        
        if len(losses) == 0:
            return 0.0
        
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = abs(losses.mean())
        
        if avg_loss == 0:
            return 0.0
        
        return avg_win / avg_loss
    
    def _avg_holding_period(self, trades: pd.DataFrame) -> float:
        """Calculate average holding period in hours."""
        if 'entry_time' not in trades.columns or 'exit_time' not in trades.columns:
            return 0.0
        
        holding_periods = []
        for _, trade in trades.iterrows():
            entry = trade['entry_time']
            exit_time = trade['exit_time']
            
            if pd.notna(entry) and pd.notna(exit_time):
                duration = (exit_time - entry).total_seconds() / 3600
                holding_periods.append(duration)
        
        if not holding_periods:
            return 0.0
        
        return np.mean(holding_periods)
    
    def calculate_information_coefficient(
        self,
        alpha_scores: pd.Series,
        forward_returns: pd.Series
    ) -> float:
        """
        Calculate Information Coefficient (IC).
        
        IC measures correlation between alpha scores and actual forward returns.
        Higher IC = better predictive power.
        
        Args:
            alpha_scores: Alpha scores from strategy
            forward_returns: Actual forward returns
        
        Returns:
            IC (correlation coefficient)
        """
        if len(alpha_scores) != len(forward_returns):
            return 0.0
        
        # Remove NaN values
        valid_mask = ~(alpha_scores.isna() | forward_returns.isna())
        alpha_clean = alpha_scores[valid_mask]
        returns_clean = forward_returns[valid_mask]
        
        if len(alpha_clean) < 2:
            return 0.0
        
        return alpha_clean.corr(returns_clean)
