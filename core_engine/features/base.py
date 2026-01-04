"""
Base feature computation interface.
"""
from abc import ABC, abstractmethod
import pandas as pd


class FeatureComputer(ABC):
    """Base interface for feature computation."""
    
    name: str = "base_feature"
    
    @abstractmethod
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute features from OHLCV data.
        
        Args:
            df: DataFrame with columns [timestamp, open, high, low, close, volume]
        
        Returns:
            DataFrame with new feature columns added
        """
        pass
    
    def validate_input(self, df: pd.DataFrame) -> None:
        """Validate input DataFrame has required columns."""
        required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing = set(required) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
