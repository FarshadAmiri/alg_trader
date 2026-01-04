"""
Liquidity and volume-based features.
"""
import pandas as pd
import numpy as np
from .base import FeatureComputer


class LiquidityFeatures(FeatureComputer):
    """Compute volume and liquidity indicators."""
    
    name = "liquidity"
    
    def __init__(self, volume_ma_period: int = 20):
        self.volume_ma_period = volume_ma_period
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute liquidity features."""
        self.validate_input(df)
        
        df = df.copy()
        
        # Volume moving average
        df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Volume z-score (standardized volume)
        volume_mean = df['volume'].rolling(window=self.volume_ma_period).mean()
        volume_std = df['volume'].rolling(window=self.volume_ma_period).std()
        df['volume_zscore'] = (df['volume'] - volume_mean) / volume_std
        
        # Volume trend
        df['volume_trend_5'] = df['volume'].pct_change(5)
        
        # VWAP (Volume Weighted Average Price) - approximation
        df['vwap'] = (df['close'] * df['volume']).rolling(window=20).sum() / df['volume'].rolling(window=20).sum()
        df['price_vwap_ratio'] = df['close'] / df['vwap']
        
        # On-Balance Volume (OBV)
        df['obv'] = self._compute_obv(df)
        df['obv_ema'] = df['obv'].ewm(span=20, adjust=False).mean()
        
        return df
    
    def _compute_obv(self, df: pd.DataFrame) -> pd.Series:
        """Compute On-Balance Volume."""
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i - 1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i - 1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        
        return pd.Series(obv, index=df.index)


class CompositeFeatures(FeatureComputer):
    """Compute composite features combining multiple indicators."""
    
    name = "composite"
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute composite scores.
        
        Note: This assumes momentum, volatility, and liquidity features
        have already been computed.
        """
        df = df.copy()
        
        # Momentum score (normalized)
        if 'rsi_distance_50' in df.columns and 'macd_histogram' in df.columns:
            rsi_norm = df['rsi_distance_50'] / 50.0  # -1 to 1
            macd_norm = np.tanh(df['macd_histogram'])  # bounded
            df['momentum_score'] = (rsi_norm + macd_norm) / 2
        
        # Volatility-adjusted momentum
        if 'momentum_score' in df.columns and 'atr_pct' in df.columns:
            df['vol_adj_momentum'] = df['momentum_score'] / (1 + df['atr_pct'] / 100)
        
        # Volume-weighted momentum
        if 'momentum_score' in df.columns and 'volume_zscore' in df.columns:
            df['vol_weighted_momentum'] = df['momentum_score'] * (1 + df['volume_zscore'] / 10)
        
        return df
