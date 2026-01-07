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
    Positions are closed based on strategy exit conditions, not fixed time.
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
            window_hours: Maximum holding period in hours (used as safety limit)
            shift_hours: Window shift interval in hours (evaluation frequency)
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
        
        For short-term strategies: If shift_hours <= 0.5, evaluates every available
        data point instead of fixed time intervals.
        
        Args:
            strategy: TradingStrategy instance
            features_by_symbol: Dict mapping symbol -> features DataFrame
            start_time: Backtest start time
            end_time: Backtest end time
        
        Returns:
            List of TradeResult objects
        """
        results = []
        
        # For very short-term strategies, check every bar instead of fixed intervals
        if self.shift_hours <= 0.5:
            print(f"[DEBUG] Short-term mode: checking every available candle")
            results = self._run_bar_by_bar(strategy, features_by_symbol, start_time, end_time)
        else:
            results = self._run_time_interval(strategy, features_by_symbol, start_time, end_time)
        
        print(f"[DEBUG] Backtest complete: {len(results)} trades")
        return results
    
    def _run_bar_by_bar(
        self,
        strategy,
        features_by_symbol: Dict[str, pd.DataFrame],
        start_time: datetime,
        end_time: datetime
    ) -> List[TradeResult]:
        """
        Run backtest checking every available data point.
        
        Used for short-term strategies where we need to check every candle.
        """
        results = []
        
        # Get all unique timestamps across all symbols
        all_timestamps = set()
        for features in features_by_symbol.values():
            if 'timestamp' in features.columns:
                timestamps = features[
                    (features['timestamp'] >= start_time) & 
                    (features['timestamp'] <= end_time)
                ]['timestamp'].unique()
                all_timestamps.update(timestamps)
        
        sorted_timestamps = sorted(all_timestamps)
        print(f"[DEBUG] Checking {len(sorted_timestamps)} time points from {start_time} to {end_time}")
        
        evaluated_count = 0
        for current_time in sorted_timestamps:
            evaluated_count += 1
            
            # Select symbols at current time
            selected_symbols = strategy.select_symbols(
                features_by_symbol,
                current_time
            )
            
            if evaluated_count % 100 == 0 or selected_symbols:
                print(f"[DEBUG] Time {evaluated_count}/{len(sorted_timestamps)} ({current_time}): {len(selected_symbols)} symbols selected")
            
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
                    # Evaluate trade using strategy's exit conditions
                    trade_result = self._evaluate_trade_with_exit_strategy(
                        strategy,
                        symbol,
                        features_by_symbol[symbol],
                        current_time,
                        end_time
                    )
                    
                    if trade_result:
                        results.append(trade_result)
                        hold_hours = (trade_result.exit_time - trade_result.entry_time).total_seconds() / 3600
                        print(f"[DEBUG]   ✓ Trade: {symbol} {trade_result.return_pct:.2f}% (held {hold_hours:.1f}h)")
        
        return results
    
    def _run_time_interval(
        self,
        strategy,
        features_by_symbol: Dict[str, pd.DataFrame],
        start_time: datetime,
        end_time: datetime
    ) -> List[TradeResult]:
        """
        Run backtest at fixed time intervals.
        
        Traditional walk-forward approach for longer-term strategies.
        """
        results = []
        
        current_time = start_time
        window_count = 0
        
        while current_time <= end_time:
            window_count += 1
            
            # Select symbols at current time
            selected_symbols = strategy.select_symbols(
                features_by_symbol,
                current_time
            )
            
            print(f"[DEBUG] Window #{window_count} at {current_time}: {len(selected_symbols)} symbols selected: {selected_symbols}")
            
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
                
                print(f"[DEBUG]   {symbol} signal: {signal}")
                
                if signal == "LONG":
                    # Evaluate trade using strategy's exit conditions
                    trade_result = self._evaluate_trade_with_exit_strategy(
                        strategy,
                        symbol,
                        features_by_symbol[symbol],
                        current_time,
                        end_time
                    )
                    
                    if trade_result:
                        results.append(trade_result)
                        print(f"[DEBUG]   Trade recorded: {symbol} {trade_result.return_pct:.2f}% (held {(trade_result.exit_time - trade_result.entry_time).total_seconds()/3600:.1f}h)")
            
            # Move to next window
            current_time += timedelta(hours=self.shift_hours)
        
        print(f"[DEBUG] Backtest complete: {window_count} windows, {len(results)} trades")
        return results
    
    def _evaluate_trade_with_exit_strategy(
        self,
        strategy,
        symbol: str,
        features: pd.DataFrame,
        entry_time: datetime,
        max_exit_time: datetime
    ) -> Optional[TradeResult]:
        """
        Evaluate a trade using strategy's exit conditions.
        
        Instead of fixed time window, checks at each data point if the
        strategy wants to close the position.
        
        Args:
            strategy: TradingStrategy instance with should_close_position method
            symbol: Trading symbol
            features: Features DataFrame
            entry_time: Entry timestamp
            max_exit_time: Maximum allowed exit time (backtest end boundary)
        
        Returns:
            TradeResult or None if data unavailable
        """
        # Get entry price
        entry_data = self._get_price_at_time(features, entry_time)
        if entry_data is None:
            return None
        
        entry_price = entry_data['close']
        
        # Get all data points after entry
        future_data = features[
            (features['timestamp'] > entry_time) &
            (features['timestamp'] <= max_exit_time)
        ].copy()
        
        if future_data.empty:
            return None
        
        # Check each time point for exit signal
        exit_time = None
        exit_price = None
        
        for idx, row in future_data.iterrows():
            current_time = row['timestamp']
            current_price = row['close']
            
            # Ask strategy if we should close
            should_exit = strategy.should_close_position(
                symbol=symbol,
                features=features,
                entry_time=entry_time,
                current_time=current_time,
                entry_price=entry_price,
                current_price=current_price
            )
            
            if should_exit:
                exit_time = current_time
                exit_price = current_price
                break
        
        # If no exit signal, use last available price
        if exit_time is None:
            exit_time = future_data.iloc[-1]['timestamp']
            exit_price = future_data.iloc[-1]['close']
        
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
            metadata={
                'exit_reason': 'strategy_signal' if exit_time != future_data.iloc[-1]['timestamp'] else 'max_time'
            }
        )
    
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
