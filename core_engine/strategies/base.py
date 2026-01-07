"""
Base strategy interface.
"""
from abc import ABC, abstractmethod
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime


class TradingStrategy(ABC):
    """Base interface for trading strategies."""
    
    name: str = "base_strategy"
    
    # Strategy metadata (define in subclasses)
    preferred_timeframe: str = "5m"              # Optimal candle timeframe
    evaluation_mode: str = "periodic"            # "every_bar" or "periodic"
    evaluation_interval_hours: float = 2.0       # If periodic, check every N hours
    max_hold_hours: float = 4.0                  # Maximum position hold time
    typical_hold_range: str = "1-4 hours"        # Human-readable typical hold
    
    def __init__(self, parameters: Optional[Dict] = None):
        """
        Initialize strategy with parameters.
        
        Args:
            parameters: Dictionary of strategy-specific parameters
        """
        self.parameters = parameters or {}
    
    @abstractmethod
    def select_symbols(
        self,
        features_by_symbol: Dict[str, pd.DataFrame],
        current_time: datetime
    ) -> List[str]:
        """
        Select symbols to trade at current time.
        
        Args:
            features_by_symbol: Dict mapping symbol -> DataFrame with features
            current_time: Current evaluation timestamp
        
        Returns:
            List of selected symbols (ranked by preference)
        """
        pass
    
    @abstractmethod
    def generate_signal(
        self,
        symbol: str,
        features: pd.DataFrame,
        current_time: datetime
    ) -> str:
        """
        Generate trading signal for a specific symbol.
        
        Args:
            symbol: Symbol to evaluate
            features: DataFrame with computed features
            current_time: Current evaluation timestamp
        
        Returns:
            "LONG", "SHORT", or "FLAT"
        """
        pass
    
    @abstractmethod
    def should_close_position(
        self,
        symbol: str,
        features: pd.DataFrame,
        entry_time: datetime,
        current_time: datetime,
        entry_price: float,
        current_price: float
    ) -> bool:
        """
        Determine if an open position should be closed.
        
        This allows each strategy to define its own exit logic based on:
        - Technical indicators (e.g., RSI overbought, MACD crossover)
        - Profit targets or stop losses
        - Time-based exits (if desired)
        - Market conditions
        
        Args:
            symbol: Symbol of the open position
            features: DataFrame with computed features
            entry_time: When the position was entered
            current_time: Current evaluation timestamp
            entry_price: Price at entry
            current_price: Current market price
        
        Returns:
            True if position should be closed, False otherwise
        """
        pass
    
    def get_latest_features(
        self,
        features: pd.DataFrame,
        current_time: datetime
    ) -> Optional[pd.Series]:
        """
        Get the latest feature row at or before current_time.
        
        Args:
            features: DataFrame with features
            current_time: Current evaluation timestamp
        
        Returns:
            Latest feature row as Series, or None if not available
        """
        if features.empty:
            return None
        
        # Ensure timestamp column exists
        if 'timestamp' not in features.columns:
            return None
        
        # Filter to data at or before current_time
        valid_data = features[features['timestamp'] <= current_time]
        
        if valid_data.empty:
            return None
        
        # Return the last row
        return valid_data.iloc[-1]
