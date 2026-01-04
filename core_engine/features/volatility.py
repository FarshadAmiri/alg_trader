"""
Volatility-based features.
"""
import pandas as pd
import numpy as np
from .base import FeatureComputer


class VolatilityFeatures(FeatureComputer):
    """Compute volatility-based indicators."""
    
    name = "volatility"
    
    def __init__(
        self,
        atr_period: int = 14,
        bb_period: int = 20,
        bb_std: float = 2.0
    ):
        self.atr_period = atr_period
        self.bb_period = bb_period
        self.bb_std = bb_std
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute volatility features."""
        self.validate_input(df)
        
        df = df.copy()
        
        # ATR (Average True Range)
        df['atr'] = self._compute_atr(df, self.atr_period)
        df['atr_pct'] = (df['atr'] / df['close']) * 100
        
        # Historical volatility (standard deviation of returns)
        returns = df['close'].pct_change()
        df['volatility_10'] = returns.rolling(window=10).std() * 100
        df['volatility_20'] = returns.rolling(window=20).std() * 100
        
        # Bollinger Bands
        sma = df['close'].rolling(window=self.bb_period).mean()
        std = df['close'].rolling(window=self.bb_period).std()
        
        df['bb_upper'] = sma + (self.bb_std * std)
        df['bb_middle'] = sma
        df['bb_lower'] = sma - (self.bb_std * std)
        df['bb_width'] = ((df['bb_upper'] - df['bb_lower']) / df['bb_middle']) * 100
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        return df
    
    def _compute_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Compute Average True Range."""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr


class RangeFeatures(FeatureComputer):
    """Compute price range features."""
    
    name = "range"
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute range-based features."""
        self.validate_input(df)
        
        df = df.copy()
        
        # Daily range
        df['candle_range'] = df['high'] - df['low']
        df['candle_range_pct'] = (df['candle_range'] / df['close']) * 100
        
        # Body size
        df['candle_body'] = abs(df['close'] - df['open'])
        df['candle_body_pct'] = (df['candle_body'] / df['close']) * 100
        
        # Wick sizes
        df['upper_wick'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
        
        return df
