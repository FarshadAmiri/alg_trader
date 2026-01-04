"""
Walk-forward backtesting engine.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TradeResult:
    """Result of a single backtest window trade."""
    symbol: str
    entry_time: datetime
    exit_time: datetime
    direction: str
    return_pct: float
    max_drawdown: float
    metadata: Dict


class WalkForwardEngine:
    """
    Walk-forward sliding window backtester.
    
    Evaluates strategy performance using overlapping time windows.
    """
    
    def __init__(
        self,
        window_hours: int = 4,
        shift_hours: int = 2,
        fee_bps: int = 10,
        slippage_bps: int = 0
    ):
        """
        Initialize walk-forward engine.
        
        Args:
            window_hours: Holding period in hours
            shift_hours: Window shift interval in hours
            fee_bps: Trading fee in basis points (10 = 0.10%)
            slippage_bps: Slippage in basis points
        """
        self.window_hours = window_hours
        self.shift_hours = shift_hours
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
    
    def run_backtest(
        self,
        strategy,
        features_by_symbol: Dict[str, pd.DataFrame],
        start_time: datetime,
        end_time: datetime
    ) -> List[TradeResult]:
        """
        Run walk-forward backtest.
        
        Args:
            strategy: TradingStrategy instance
            features_by_symbol: Dict mapping symbol -> features DataFrame
            start_time: Backtest start time
            end_time: Backtest end time
        
        Returns:
            List of TradeResult objects
        """
        results = []
        
        current_time = start_time
        
        while current_time <= end_time:
            # Select symbols at current time
            selected_symbols = strategy.select_symbols(
                features_by_symbol,
                current_time
            )
            
            # Evaluate each selected symbol
            for symbol in selected_symbols:
                if symbol not in features_by_symbol:
                    continue
                
                # Generate signal
                signal = strategy.generate_signal(
                    symbol,
                    features_by_symbol[symbol],
                    current_time
                )
                
                if signal == "LONG":
                    # Evaluate trade over the holding window
                    trade_result = self._evaluate_trade(
                        symbol,
                        features_by_symbol[symbol],
                        current_time,
                        current_time + timedelta(hours=self.window_hours)
                    )
                    
                    if trade_result:
                        results.append(trade_result)
            
            # Move to next window
            current_time += timedelta(hours=self.shift_hours)
        
        return results
    
    def _evaluate_trade(
        self,
        symbol: str,
        features: pd.DataFrame,
        entry_time: datetime,
        exit_time: datetime
    ) -> Optional[TradeResult]:
        """
        Evaluate a single trade over the holding period.
        
        Args:
            symbol: Trading symbol
            features: Features DataFrame
            entry_time: Entry timestamp
            exit_time: Exit timestamp
        
        Returns:
            TradeResult or None if data unavailable
        """
        # Get entry price
        entry_data = self._get_price_at_time(features, entry_time)
        if entry_data is None:
            return None
        
        entry_price = entry_data['close']
        
        # Get exit price
        exit_data = self._get_price_at_time(features, exit_time)
        if exit_data is None:
            # Use latest available price if exact exit time not available
            exit_data = self._get_latest_price_before(features, exit_time)
            if exit_data is None:
                return None
        
        exit_price = exit_data['close']
        
        # Calculate gross return
        gross_return_pct = ((exit_price - entry_price) / entry_price) * 100
        
        # Apply fees and slippage
        total_cost_bps = (self.fee_bps * 2) + self.slippage_bps  # Round trip
        cost_pct = total_cost_bps / 100  # Convert bps to %
        
        net_return_pct = gross_return_pct - cost_pct
        
        # Calculate max drawdown during holding period
        max_dd = self._calculate_max_drawdown(
            features,
            entry_time,
            exit_time,
            entry_price
        )
        
        return TradeResult(
            symbol=symbol,
            entry_time=entry_time,
            exit_time=exit_time,
            direction="LONG",
            return_pct=net_return_pct,
            max_drawdown=max_dd,
            metadata={}
        )
    
    def _get_price_at_time(
        self,
        features: pd.DataFrame,
        timestamp: datetime
    ) -> Optional[pd.Series]:
        """Get price data at specific timestamp."""
        if features.empty or 'timestamp' not in features.columns:
            return None
        
        # Find exact match or nearest
        matches = features[features['timestamp'] == timestamp]
        
        if not matches.empty:
            return matches.iloc[0]
        
        return None
    
    def _get_latest_price_before(
        self,
        features: pd.DataFrame,
        timestamp: datetime
    ) -> Optional[pd.Series]:
        """Get latest price data before or at timestamp."""
        if features.empty or 'timestamp' not in features.columns:
            return None
        
        valid_data = features[features['timestamp'] <= timestamp]
        
        if valid_data.empty:
            return None
        
        return valid_data.iloc[-1]
    
    def _calculate_max_drawdown(
        self,
        features: pd.DataFrame,
        start_time: datetime,
        end_time: datetime,
        entry_price: float
    ) -> float:
        """
        Calculate maximum drawdown during holding period.
        
        Args:
            features: Features DataFrame
            start_time: Start of period
            end_time: End of period
            entry_price: Entry price (reference)
        
        Returns:
            Max drawdown as percentage
        """
        if features.empty or 'timestamp' not in features.columns:
            return 0.0
        
        # Get price data in the window
        window_data = features[
            (features['timestamp'] >= start_time) &
            (features['timestamp'] <= end_time)
        ]
        
        if window_data.empty or 'close' not in window_data.columns:
            return 0.0
        
        # Calculate drawdown from entry price
        prices = window_data['close'].values
        drawdowns = ((prices - entry_price) / entry_price) * 100
        
        # Max drawdown is the most negative value
        max_dd = abs(min(drawdowns.min(), 0))
        
        return max_dd
