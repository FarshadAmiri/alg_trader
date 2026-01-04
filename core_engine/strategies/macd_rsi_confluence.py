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
        if not all(col in row.index for col in required):
            return False
        
        # RSI filter
        if row['rsi'] < self.parameters['rsi_min'] or row['rsi'] > self.parameters['rsi_max']:
            return False
        
        # MACD filter
        if row['macd_histogram'] < self.parameters['macd_hist_min']:
            return False
        
        # Volatility filter
        if row['atr_pct'] > self.parameters['atr_pct_max']:
            return False
        
        # Volume filter
        if row['volume_ratio'] < self.parameters['volume_min_ratio']:
            return False
        
        return True
    
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
