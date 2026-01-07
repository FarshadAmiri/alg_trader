import sys
from core_engine.data.providers import BinanceDirectProvider
from datetime import datetime, timedelta

provider = BinanceDirectProvider()
end = datetime.now()
start = end - timedelta(days=1)

print('Testing BTCUSDT fetch with Direct Binance API...')
df = provider.fetch_ohlcv('BTCUSDT', '5m', start, end)
print(f'Result: {len(df)} rows')

if not df.empty:
    print('SUCCESS!')
    print(df.head())
    print(f'\nFirst timestamp: {df.iloc[0]["timestamp"]}')
    print(f'Last timestamp: {df.iloc[-1]["timestamp"]}')
else:
    print('FAILED - empty DataFrame')
