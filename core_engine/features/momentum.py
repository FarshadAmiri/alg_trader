"""
Momentum-based feature indicators.
"""
import pandas as pd
import numpy as np
from .base import FeatureComputer


class MomentumFeatures(FeatureComputer):
    """Compute momentum-based technical indicators."""
    
    name = "momentum"
    
    def __init__(
        self,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9
    ):
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute momentum features."""
        self.validate_input(df)
        
        df = df.copy()
        
        # RSI
        df['rsi'] = self._compute_rsi(df['close'], self.rsi_period)
        df['rsi_distance_50'] = df['rsi'] - 50.0  # Distance from neutral
        
        # MACD
        macd_line, signal_line, histogram = self._compute_macd(
            df['close'],
            self.macd_fast,
            self.macd_slow,
            self.macd_signal
        )
        df['macd_line'] = macd_line
        df['macd_signal'] = signal_line
        df['macd_histogram'] = histogram
        
        # MACD histogram slope (momentum of momentum)
        df['macd_hist_slope'] = df['macd_histogram'].diff()
        
        # Simple price momentum
        df['price_momentum_1'] = df['close'].pct_change(1)
        df['price_momentum_5'] = df['close'].pct_change(5)
        df['price_momentum_10'] = df['close'].pct_change(10)
        
        # EMA distances
        ema_12 = df['close'].ewm(span=12, adjust=False).mean()
        ema_26 = df['close'].ewm(span=26, adjust=False).mean()
        df['ema_12_26_distance'] = (ema_12 - ema_26) / ema_26
        
        return df
    
    def _compute_rsi(self, prices: pd.Series, period: int) -> pd.Series:
        """Compute RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _compute_macd(
        self,
        prices: pd.Series,
        fast: int,
        slow: int,
        signal: int
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Compute MACD indicator."""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram


class TrendFeatures(FeatureComputer):
    """Compute trend-based features."""
    
    name = "trend"
    
    def __init__(self, sma_periods: list[int] = None):
        self.sma_periods = sma_periods or [20, 50, 200]
    
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute trend features."""
        self.validate_input(df)
        
        df = df.copy()
        
        # Simple Moving Averages
        for period in self.sma_periods:
            if len(df) >= period:
                df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
                df[f'price_sma_{period}_ratio'] = df['close'] / df[f'sma_{period}']
        
        # Trend slope (linear regression)
        df['trend_slope_5'] = self._compute_slope(df['close'], window=5)
        df['trend_slope_10'] = self._compute_slope(df['close'], window=10)
        
        return df
    
    def _compute_slope(self, series: pd.Series, window: int) -> pd.Series:
        """Compute rolling linear regression slope."""
        slopes = []
        for i in range(len(series)):
            if i < window - 1:
                slopes.append(np.nan)
            else:
                y = series.iloc[i - window + 1:i + 1].values
                x = np.arange(window)
                slope = np.polyfit(x, y, 1)[0]
                slopes.append(slope)
        
        return pd.Series(slopes, index=series.index)
