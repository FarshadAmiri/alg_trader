"""
Exchange provider interfaces and implementations.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
import pandas as pd


class ExchangeProvider(ABC):
    """Base interface for exchange data providers."""
    
    @abstractmethod
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data for a symbol.
        
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        pass
    
    @abstractmethod
    def get_available_symbols(self) -> List[str]:
        """Return list of available trading symbols."""
        pass


class NobitexProvider(ExchangeProvider):
    """
    Nobitex exchange provider.
    API docs: https://apidocs.nobitex.ir/en/
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.nobitex.ir"
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch OHLCV from Nobitex.
        
        Note: Implementation requires requests library and proper API handling.
        This is a stub that should be completed based on Nobitex API documentation.
        """
        import requests
        from datetime import timezone
        
        # Convert timeframe to Nobitex format
        timeframe_map = {
            '5m': '5',
            '15m': '15',
            '30m': '30',
            '1h': '60',
            '3h': '180',
            '4h': '240',
            '1d': 'D',
        }
        
        tf = timeframe_map.get(timeframe, timeframe)
        
        # Convert timestamps to Unix timestamp
        start_ts = int(start_time.replace(tzinfo=timezone.utc).timestamp())
        end_ts = int(end_time.replace(tzinfo=timezone.utc).timestamp())
        
        # API endpoint (adjust based on actual Nobitex API)
        # This is a placeholder - actual implementation depends on API structure
        url = f"{self.base_url}/market/udf/history"
        
        params = {
            'symbol': symbol,
            'resolution': tf,
            'from': start_ts,
            'to': end_ts,
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Parse response (structure depends on actual API)
            # Placeholder structure - adjust based on real API response
            if data.get('s') != 'ok':
                return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            df = pd.DataFrame({
                'timestamp': pd.to_datetime(data['t'], unit='s'),
                'open': data['o'],
                'high': data['h'],
                'low': data['l'],
                'close': data['c'],
                'volume': data['v'],
            })
            
            return df
            
        except Exception as e:
            print(f"Error fetching data from Nobitex: {e}")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols from Nobitex."""
        # Common Nobitex symbols (update based on actual API)
        return [
            'BTCUSDT',
            'ETHUSDT',
            'LTCUSDT',
            'XRPUSDT',
            'BNBUSDT',
            'ADAUSDT',
            'DOGEUSDT',
            'DOTUSDT',
        ]


class CCXTProvider(ExchangeProvider):
    """
    Generic CCXT-based provider for multiple exchanges.
    Requires ccxt library: pip install ccxt
    """
    
    def __init__(self, exchange_name: str = 'binance', api_key: Optional[str] = None, api_secret: Optional[str] = None):
        try:
            import ccxt
        except ImportError:
            raise ImportError("ccxt library required. Install with: pip install ccxt")
        
        exchange_class = getattr(ccxt, exchange_name)
        self.exchange = exchange_class({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Fetch OHLCV using CCXT."""
        try:
            # Convert to milliseconds
            since = int(start_time.timestamp() * 1000)
            
            all_candles = []
            while True:
                candles = self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe,
                    since=since,
                    limit=limit or 1000
                )
                
                if not candles:
                    break
                
                all_candles.extend(candles)
                
                # Check if we've reached end_time
                last_timestamp = candles[-1][0]
                if datetime.fromtimestamp(last_timestamp / 1000) >= end_time:
                    break
                
                since = last_timestamp + 1
            
            # Convert to DataFrame
            df = pd.DataFrame(
                all_candles,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Filter to requested time range
            df = df[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]
            
            return df
            
        except Exception as e:
            print(f"Error fetching data via CCXT: {e}")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_available_symbols(self) -> List[str]:
        """Get available symbols from exchange."""
        try:
            markets = self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            print(f"Error fetching symbols: {e}")
            return []
