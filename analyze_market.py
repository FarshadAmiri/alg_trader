"""
Analyze market conditions to understand why strategy didn't trade.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from trading.models import Candle
from core_engine.features.momentum import MomentumFeatures
from core_engine.features.volatility import VolatilityFeatures
from core_engine.features.liquidity import LiquidityFeatures, CompositeFeatures
import pandas as pd

# Get ETHUSDT data
print("Loading ETHUSDT candles...")
df = pd.DataFrame(list(Candle.objects.filter(symbol='ETHUSDT').order_by('timestamp').values()))

if df.empty:
    print("No data found!")
    exit()

print(f"Data: {len(df)} candles from {df['timestamp'].min()} to {df['timestamp'].max()}")

# Compute features
print("\nComputing features...")
mf = MomentumFeatures()
vf = VolatilityFeatures()
lf = LiquidityFeatures()
cf = CompositeFeatures()

df = mf.compute(df)
df = vf.compute(df)
df = lf.compute(df)
df = cf.compute(df)

# Drop NaN rows
df_clean = df.dropna()
print(f"Clean data: {len(df_clean)} rows after dropping NaN")

# Analyze BB position
print("\n" + "="*60)
print("BOLLINGER BAND POSITION ANALYSIS")
print("="*60)
print(df_clean['bb_position'].describe())
print(f"\nLowest bb_position: {df_clean['bb_position'].min():.4f}")
print(f"Times price touched lower band (bb_position < 0.2): {(df_clean['bb_position'] < 0.2).sum()}")

# Analyze RSI
print("\n" + "="*60)
print("RSI ANALYSIS")
print("="*60)
print(df_clean['rsi'].describe())
print(f"\nTimes RSI < 30 (oversold): {(df_clean['rsi'] < 30).sum()}")
print(f"Lowest RSI: {df_clean['rsi'].min():.2f}")

# Analyze Volume
print("\n" + "="*60)
print("VOLUME ANALYSIS")
print("="*60)
print(df_clean['volume_ratio'].describe())
print(f"\nTimes volume > 1.2x average: {(df_clean['volume_ratio'] > 1.2).sum()}")

# Analyze Volatility
print("\n" + "="*60)
print("VOLATILITY ANALYSIS")
print("="*60)
print(df_clean['atr_pct'].describe())
print(f"\nTimes ATR < 4% (low vol): {(df_clean['atr_pct'] < 4.0).sum()}")

# Check for strategy setups
print("\n" + "="*60)
print("MEAN REVERSION SETUP ANALYSIS")
print("="*60)

# Individual conditions
bb_touch = df_clean['bb_position'] < 0.2
rsi_oversold = df_clean['rsi'] < 30
vol_spike = df_clean['volume_ratio'] > 1.2
low_vol = df_clean['atr_pct'] < 4.0

print(f"BB lower touch (< 0.2):     {bb_touch.sum():4d} times")
print(f"RSI oversold (< 30):        {rsi_oversold.sum():4d} times")
print(f"Volume spike (> 1.2x):      {vol_spike.sum():4d} times")
print(f"Low volatility (< 4% ATR):  {low_vol.sum():4d} times")

# Combined conditions
bb_and_rsi = df_clean[(df_clean['bb_position'] < 0.2) & (df_clean['rsi'] < 30)]
print(f"\nBB touch + RSI oversold:    {len(bb_and_rsi):4d} times")

all_conditions = df_clean[
    (df_clean['bb_position'] < 0.2) & 
    (df_clean['rsi'] < 30) & 
    (df_clean['volume_ratio'] > 1.2) & 
    (df_clean['atr_pct'] < 4.0)
]
print(f"ALL CONDITIONS MET:         {len(all_conditions):4d} times")

if len(all_conditions) > 0:
    print("\nFull setups found at:")
    for idx, row in all_conditions.iterrows():
        print(f"  {row['timestamp']} - Price: ${row['close']:.2f}, RSI: {row['rsi']:.1f}, BB pos: {row['bb_position']:.3f}")

# Show what WOULD have qualified with relaxed parameters
print("\n" + "="*60)
print("RELAXED PARAMETERS (to find trades)")
print("="*60)

relaxed = df_clean[
    (df_clean['bb_position'] < 0.35) &  # More relaxed
    (df_clean['rsi'] < 40) &            # Less extreme
    (df_clean['volume_ratio'] > 1.0) &  # Any above-average volume
    (df_clean['atr_pct'] < 5.0)         # Slightly higher vol OK
]
print(f"With relaxed params: {len(relaxed)} setups")

if len(relaxed) > 0:
    print("\nTop 5 relaxed setups:")
    relaxed_sorted = relaxed.sort_values('bb_position').head(5)
    for idx, row in relaxed_sorted.iterrows():
        print(f"  {row['timestamp']} - Price: ${row['close']:.2f}, RSI: {row['rsi']:.1f}, BB pos: {row['bb_position']:.3f}, Vol: {row['volume_ratio']:.2f}x")

# Market regime analysis
print("\n" + "="*60)
print("MARKET REGIME")
print("="*60)
avg_bb_pos = df_clean['bb_position'].mean()
avg_rsi = df_clean['rsi'].mean()

if avg_bb_pos > 0.6:
    print("⚠ Market was STRONG/OVERBOUGHT (not good for mean reversion)")
elif avg_bb_pos < 0.4:
    print("✓ Market was WEAK/OVERSOLD (good for mean reversion)")
else:
    print("→ Market was NEUTRAL/RANGING")

print(f"Average BB position: {avg_bb_pos:.2f} (0.5 = middle)")
print(f"Average RSI: {avg_rsi:.1f} (50 = neutral)")

if avg_rsi > 60:
    print("Market was in uptrend - mean reversion less effective")
elif avg_rsi < 40:
    print("Market was in downtrend - good for bounce trades")
else:
    print("Market was balanced")
