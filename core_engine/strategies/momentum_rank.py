"""
Momentum rank-based strategy.
"""
import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime
from .base import TradingStrategy


class MomentumRankStrategy(TradingStrategy):
    """
    Strategy that ranks symbols by momentum score.
    
    Selects top N symbols with:
    - Positive momentum across multiple timeframes
    - Strong volume confirmation
    - Controlled volatility
    """
    
    name = "momentum_rank"
    
    def __init__(self, parameters: Dict = None):
        default_params = {
            'min_momentum_score': 0.2,
            'atr_pct_max': 6.0,
            'volume_min_zscore': -0.5,
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
        """Rank symbols by momentum score."""
        candidates = []
        
        for symbol, features in features_by_symbol.items():
            latest = self.get_latest_features(features, current_time)
            
            if latest is None:
                continue
            
            if not self._passes_filters(latest):
                continue
            
            score = self._calculate_momentum_score(latest)
            
            if not np.isnan(score) and score >= self.parameters['min_momentum_score']:
                candidates.append((symbol, score))
        
        # Sort by score and return top N
        candidates.sort(key=lambda x: x[1], reverse=True)
        max_positions = self.parameters['max_positions']
        
        return [symbol for symbol, score in candidates[:max_positions]]
    
    def generate_signal(
        self,
        symbol: str,
        features: pd.DataFrame,
        current_time: datetime
    ) -> str:
        """Generate signal based on momentum."""
        latest = self.get_latest_features(features, current_time)
        
        if latest is None:
            return "FLAT"
        
        if not self._passes_filters(latest):
            return "FLAT"
        
        score = self._calculate_momentum_score(latest)
        
        if score >= self.parameters['min_momentum_score']:
            return "LONG"
        
        return "FLAT"
    
    def _passes_filters(self, row: pd.Series) -> bool:
        """Check basic filters."""
        
        # Volatility filter
        if 'atr_pct' in row.index:
            if row['atr_pct'] > self.parameters['atr_pct_max']:
                return False
        
        # Volume filter
        if 'volume_zscore' in row.index:
            if row['volume_zscore'] < self.parameters['volume_min_zscore']:
                return False
        
        return True
    
    def _calculate_momentum_score(self, row: pd.Series) -> float:
        """
        Calculate combined momentum score.
        
        Uses multiple timeframe momentum indicators.
        """
        score = 0.0
        weight_sum = 0.0
        
        # Price momentum components
        momentum_cols = {
            'price_momentum_1': 0.1,
            'price_momentum_5': 0.3,
            'price_momentum_10': 0.3,
            'macd_histogram': 0.2,
            'rsi_distance_50': 0.1,
        }
        
        for col, weight in momentum_cols.items():
            if col in row.index and not pd.isna(row[col]):
                value = row[col]
                
                # Normalize different indicators
                if col.startswith('price_momentum'):
                    normalized = np.tanh(value * 10)  # Scale percentage
                elif col == 'macd_histogram':
                    normalized = np.tanh(value)
                elif col == 'rsi_distance_50':
                    normalized = value / 50.0
                else:
                    normalized = value
                
                score += normalized * weight
                weight_sum += weight
        
        if weight_sum > 0:
            score /= weight_sum
        
        return score
