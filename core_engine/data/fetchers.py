"""
Data fetching and normalization utilities.
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
from .providers import ExchangeProvider


class DataFetcher:
    """Fetches and normalizes market data."""
    
    def __init__(self, provider: ExchangeProvider):
        self.provider = provider
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data and ensure proper normalization.
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        df = self.provider.fetch_ohlcv(symbol, timeframe, start_time, end_time)
        
        if df.empty:
            return df
        
        # Ensure timezone-aware timestamps (UTC)
        if df['timestamp'].dt.tz is None:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize('UTC')
        else:
            df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['timestamp'], keep='last')
        
        # Validate data
        df = self._validate_candles(df)
        
        return df
    
    def _validate_candles(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean candle data."""
        if df.empty:
            return df
        
        # Remove rows with missing values
        df = df.dropna()
        
        # Ensure positive prices and volumes
        df = df[
            (df['open'] > 0) &
            (df['high'] > 0) &
            (df['low'] > 0) &
            (df['close'] > 0) &
            (df['volume'] >= 0)
        ]
        
        # Ensure high >= low
        df = df[df['high'] >= df['low']]
        
        # Ensure high >= open, close and low <= open, close
        df = df[
            (df['high'] >= df['open']) &
            (df['high'] >= df['close']) &
            (df['low'] <= df['open']) &
            (df['low'] <= df['close'])
        ]
        
        return df
    
    def resample_timeframe(
        self,
        df: pd.DataFrame,
        target_timeframe: str
    ) -> pd.DataFrame:
        """
        Resample OHLCV data to a different timeframe.
        
        Args:
            df: DataFrame with OHLCV data
            target_timeframe: Target timeframe (e.g., '1h', '4h', '1d')
        
        Returns:
            Resampled DataFrame
        """
        if df.empty:
            return df
        
        df = df.set_index('timestamp')
        
        resampled = df.resample(target_timeframe).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        return resampled.reset_index()
    
    def fetch_multiple_symbols(
        self,
        symbols: List[str],
        timeframe: str,
        start_time: datetime,
        end_time: datetime
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols.
        
        Returns:
            Dictionary mapping symbol -> DataFrame
        """
        result = {}
        for symbol in symbols:
            try:
                df = self.fetch_ohlcv(symbol, timeframe, start_time, end_time)
                if not df.empty:
                    result[symbol] = df
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
        
        return result
