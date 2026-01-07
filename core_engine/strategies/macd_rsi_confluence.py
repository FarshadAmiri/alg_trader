"""
Baseline MACD + RSI confluence strategy.
"""
import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime
from .base import TradingStrategy


class MACDRSIStrategy(TradingStrategy):
    """
    Baseline rule-based strategy using MACD and RSI.
    
    Entry conditions:
    - MACD histogram > 0 (or slope > 0 for early entry)
    - RSI between 40 and 65 (healthy long zone)
    - Volatility filter: ATR/price below threshold
    - Volume confirmation: volume above average
    
    Ranks symbols by combined momentum score.
    """
    
    name = "macd_rsi_confluence"
    
    # Strategy metadata
    preferred_timeframe = "1h"              # Works well on 1-hour candles
    evaluation_mode = "periodic"            # Check periodically, not every bar
    evaluation_interval_hours = 2.0         # Check every 2 hours
    max_hold_hours = 8.0                    # Maximum 8 hour hold
    typical_hold_range = "4-8 hours"        # Typical hold duration
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'rsi_min': 40,
            'rsi_max': 65,
            'macd_hist_min': 0.0,
            'atr_pct_max': 5.0,  # Max 5% ATR
            'volume_min_ratio': 0.8,  # At least 80% of average volume
            'max_positions': 3,
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__(default_params)
    
    def select_symbols(
        self,
        features_by_symbol: Dict[str, pd.DataFrame],
        current_time: datetime
    ) -> List[str]:
        """
        Rank and select symbols based on strategy criteria.
        """
        candidates = []
        
        for symbol, features in features_by_symbol.items():
            latest = self.get_latest_features(features, current_time)
            
            if latest is None:
                continue
            
            # Check if symbol passes filters
            if not self._passes_filters(latest):
                continue
            
            # Calculate ranking score
            score = self._calculate_score(latest)
            
            if not np.isnan(score):
                candidates.append((symbol, score))
        
        # Sort by score (descending) and return top N
        candidates.sort(key=lambda x: x[1], reverse=True)
        max_positions = self.parameters['max_positions']
        
        return [symbol for symbol, score in candidates[:max_positions]]
    
    def generate_signal(
        self,
        symbol: str,
        features: pd.DataFrame,
        current_time: datetime
    ) -> str:
        """
        Generate signal for a specific symbol.
        """
        latest = self.get_latest_features(features, current_time)
        
        if latest is None:
            return "FLAT"
        
        if self._passes_filters(latest):
            return "LONG"
        
        return "FLAT"
    
    def _passes_filters(self, row: pd.Series) -> bool:
        """Check if row passes all filter conditions."""
        
        # Check required columns exist
        required = ['rsi', 'macd_histogram', 'atr_pct', 'volume_ratio']
        missing = [col for col in required if col not in row.index]
        if missing:
            print(f"[DEBUG] Missing columns: {missing}")
            return False
        
        # Check for NaN values
        nan_fields = [col for col in required if pd.isna(row[col])]
        if nan_fields:
            print(f"[DEBUG] NaN values in: {nan_fields}")
            return False
        
        # RSI filter
        if row['rsi'] < self.parameters['rsi_min'] or row['rsi'] > self.parameters['rsi_max']:
            print(f"[DEBUG] RSI filter failed: {row['rsi']} not in [{self.parameters['rsi_min']}, {self.parameters['rsi_max']}]")
            return False
        
        # MACD filter
        if row['macd_histogram'] < self.parameters['macd_hist_min']:
            print(f"[DEBUG] MACD filter failed: {row['macd_histogram']} < {self.parameters['macd_hist_min']}")
            return False
        
        # Volatility filter
        if row['atr_pct'] > self.parameters['atr_pct_max']:
            print(f"[DEBUG] ATR filter failed: {row['atr_pct']} > {self.parameters['atr_pct_max']}")
            return False
        
        # Volume filter
        if row['volume_ratio'] < self.parameters['volume_min_ratio']:
            print(f"[DEBUG] Volume filter failed: {row['volume_ratio']} < {self.parameters['volume_min_ratio']}")
            return False
        
        print(f"[DEBUG] All filters passed! RSI={row['rsi']:.1f}, MACD={row['macd_histogram']:.4f}, ATR%={row['atr_pct']:.2f}, Vol={row['volume_ratio']:.2f}")
        return True
    
    def should_close_position(
        self,
        symbol: str,
        features: pd.DataFrame,
        entry_time: datetime,
        current_time: datetime,
        entry_price: float,
        current_price: float
    ) -> bool:
        """
        Exit conditions for MACD-RSI strategy.
        
        Close position when:
        1. RSI becomes overbought (>75) - take profits
        2. MACD histogram turns negative - momentum reversal
        3. Stop loss: down >3% from entry
        4. Take profit: up >6% from entry
        5. Maximum hold time: 8 hours (fallback safety)
        """
        latest = self.get_latest_features(features, current_time)
        
        if latest is None:
            # No data available - close position for safety
            return True
        
        # Calculate current P&L
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Stop loss: -3%
        if pnl_pct < -3.0:
            return True
        
        # Take profit: +6%
        if pnl_pct > 6.0:
            return True
        
        # RSI overbought exit (take profits when momentum exhausted)
        if 'rsi' in latest.index and latest['rsi'] > 75:
            return True
        
        # MACD momentum reversal
        if 'macd_histogram' in latest.index and latest['macd_histogram'] < 0:
            return True
        
        # Maximum holding time: 8 hours (short-term trading)
        time_held = (current_time - entry_time).total_seconds() / 3600
        if time_held >= 8.0:
            return True
        
        # Continue holding
        return False
    
    def _calculate_score(self, row: pd.Series) -> float:
        """
        Calculate ranking score for a symbol.
        
        Combines:
        - RSI distance from extremes
        - MACD histogram strength
        - Volume confirmation
        """
        # RSI score (favor middle range)
        rsi_optimal = 55
        rsi_score = 1.0 - abs(row['rsi'] - rsi_optimal) / 50.0
        
        # MACD score (normalized)
        macd_score = np.tanh(row.get('macd_histogram', 0))
        
        # Volume score
        volume_score = min(row.get('volume_ratio', 1.0), 2.0) / 2.0
        
        # Volatility penalty (lower is better)
        vol_penalty = 1.0 / (1.0 + row.get('atr_pct', 2.0) / 5.0)
        
        # Combined score
        score = (
            0.3 * rsi_score +
            0.4 * macd_score +
            0.2 * volume_score +
            0.1 * vol_penalty
        )
        
        return score
