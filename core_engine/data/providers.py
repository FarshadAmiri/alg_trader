"""
Exchange provider interfaces and implementations.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
import numpy as np


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
            'options': {
                'defaultType': 'spot',
            }
        })
        self.exchange_name = exchange_name
    
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
            # Convert symbol format: BTCUSDT -> BTC/USDT
            if '/' not in symbol and len(symbol) > 3:
                # Assume format is like BTCUSDT, ETHUSDT, etc.
                if symbol.endswith('USDT'):
                    base = symbol[:-4]
                    symbol = f"{base}/USDT"
                elif symbol.endswith('USD'):
                    base = symbol[:-3]
                    symbol = f"{base}/USD"
                elif symbol.endswith('BTC'):
                    base = symbol[:-3]
                    symbol = f"{base}/BTC"
            
            print(f"Fetching {symbol} with timeframe {timeframe}")
            
            # Convert to milliseconds
            since = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)
            
            all_candles = []
            current_since = since
            
            while current_since < end_ms:
                try:
                    candles = self.exchange.fetch_ohlcv(
                        symbol,
                        timeframe,
                        since=current_since,
                        limit=limit or 1000
                    )
                    
                    if not candles:
                        break
                    
                    print(f"Fetched {len(candles)} candles")
                    all_candles.extend(candles)
                    
                    # Update since to last timestamp + 1
                    last_timestamp = candles[-1][0]
                    if last_timestamp >= end_ms:
                        break
                    
                    current_since = last_timestamp + 1
                    
                    # Safety limit to avoid infinite loops
                    if len(all_candles) > 100000:
                        print("Hit safety limit of 100k candles")
                        break
                        
                except Exception as fetch_error:
                    print(f"Error in fetch loop: {fetch_error}")
                    # If we got some data, continue with what we have
                    if all_candles:
                        break
                    raise
            
            if not all_candles:
                print("No candles fetched")
                return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert to DataFrame
            df = pd.DataFrame(
                all_candles,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Filter to requested time range
            df = df[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]
            
            print(f"Returning {len(df)} candles after filtering")
            return df
            
        except Exception as e:
            print(f"Error fetching data via CCXT: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_available_symbols(self) -> List[str]:
        """Get available symbols from exchange."""
        try:
            markets = self.exchange.load_markets()
            return list(markets.keys())
        except Exception as e:
            print(f"Error fetching symbols: {e}")
            return []


class BinanceDirectProvider(ExchangeProvider):
    """
    Direct Binance API provider without CCXT.
    Uses requests library to bypass CCXT's load_markets() call.
    """
    
    def __init__(self):
        self.base_url = "https://api.binance.com"
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Fetch OHLCV directly from Binance API."""
        try:
            import requests
            
            # Convert symbol format: BTCUSDT is correct for Binance direct API
            if '/' in symbol:
                symbol = symbol.replace('/', '')
            
            # Convert timeframe to Binance format (already compatible: 5m, 1h, etc.)
            interval = timeframe
            
            # Convert to milliseconds
            start_ms = int(start_time.timestamp() * 1000)
            end_ms = int(end_time.timestamp() * 1000)
            
            all_candles = []
            current_start = start_ms
            
            while current_start < end_ms:
                # Binance API endpoint
                url = f"{self.base_url}/api/v3/klines"
                params = {
                    'symbol': symbol,
                    'interval': interval,
                    'startTime': current_start,
                    'endTime': end_ms,
                    'limit': limit or 1000
                }
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                candles = response.json()
                
                if not candles:
                    break
                
                all_candles.extend(candles)
                
                # Update start time to last candle's close time + 1
                last_close_time = candles[-1][6]  # Close time is at index 6
                current_start = last_close_time + 1
                
                # Safety limit
                if len(all_candles) > 100000:
                    break
                
                # If we got less than requested, we're done
                if len(candles) < (limit or 1000):
                    break
            
            if not all_candles:
                return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert to DataFrame
            # Binance kline format: [open_time, open, high, low, close, volume, close_time, ...]
            df = pd.DataFrame(all_candles)
            df = df[[0, 1, 2, 3, 4, 5]]  # Keep only OHLCV columns
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            # Convert types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            # Filter to exact time range (convert datetimes to UTC if needed)
            if start_time.tzinfo is None:
                from datetime import timezone as tz
                start_time = start_time.replace(tzinfo=tz.utc)
            if end_time.tzinfo is None:
                from datetime import timezone as tz
                end_time = end_time.replace(tzinfo=tz.utc)
                
            df = df[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]
            
            return df
            
        except Exception as e:
            print(f"Error fetching from Binance: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_available_symbols(self) -> List[str]:
        """Get available symbols from Binance."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/v3/exchangeInfo", timeout=30)
            response.raise_for_status()
            data = response.json()
            return [s['symbol'] for s in data['symbols'] if s['status'] == 'TRADING']
        except Exception as e:
            print(f"Error fetching symbols: {e}")
            return []


class MockProvider(ExchangeProvider):
    """
    Mock data provider for testing purposes.
    Generates realistic-looking random OHLCV data.
    """
    
    def __init__(self, base_price: float = 50000.0, volatility: float = 0.02):
        self.base_price = base_price
        self.volatility = volatility
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Generate mock OHLCV data."""
        try:
            # Parse timeframe to minutes
            timeframe_minutes = {
                '1m': 1, '5m': 5, '15m': 15, '30m': 30,
                '1h': 60, '4h': 240, '1d': 1440
            }
            minutes = timeframe_minutes.get(timeframe, 5)
            
            # Generate timestamps
            current = start_time
            timestamps = []
            while current <= end_time:
                timestamps.append(current)
                current += timedelta(minutes=minutes)
            
            if not timestamps:
                return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Generate price data with random walk
            n = len(timestamps)
            np.random.seed(hash(symbol) % 2**32)  # Consistent seed per symbol
            
            # Random walk for close prices
            returns = np.random.normal(0, self.volatility, n)
            close_prices = self.base_price * np.exp(np.cumsum(returns))
            
            # Generate OHLC from close prices
            candles = []
            for i, (ts, close) in enumerate(zip(timestamps, close_prices)):
                # Generate open, high, low around close
                spread = close * self.volatility * 0.5
                open_price = close + np.random.uniform(-spread, spread)
                high = max(open_price, close) + abs(np.random.uniform(0, spread))
                low = min(open_price, close) - abs(np.random.uniform(0, spread))
                volume = np.random.uniform(100, 1000) * close
                
                candles.append({
                    'timestamp': ts,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume
                })
            
            df = pd.DataFrame(candles)
            return df
            
        except Exception as e:
            print(f"Error generating mock data: {e}")
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    def get_available_symbols(self) -> List[str]:
        """Return mock symbols."""
        return [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT',
            'XRPUSDT', 'DOGEUSDT', 'DOTUSDT', 'SOLUSDT'
        ]
