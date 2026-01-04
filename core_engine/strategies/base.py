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
