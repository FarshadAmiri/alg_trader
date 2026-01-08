"""
Momentum rank-based strategy.
"""
import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime
from .base import TradingStrategy, StrategySignal


class MomentumRankStrategy(TradingStrategy):
    """
    Strategy that ranks symbols by momentum score.
    
    Selects top N symbols with:
    - Positive momentum across multiple timeframes
    - Strong volume confirmation
    - Controlled volatility
    """
    
    name = "momentum_rank"
    
    # Strategy metadata
    preferred_timeframe = "15m"             # Works on 15-minute candles
    evaluation_mode = "periodic"            # Check periodically
    evaluation_interval_hours = 1.0         # Check every hour
    max_hold_hours = 6.0                    # Maximum 6 hour hold
    typical_hold_range = "2-6 hours"        # Typical hold duration
    
    # Alpha signal metadata
    default_horizon_days = 1                # Momentum typically plays out within 1 day
    requires_volatility_adjustment = False  # Already accounts for volatility via ATR filter
    
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
    
    def generate_alpha_signal(
        self,
        symbol: str,
        features: pd.DataFrame,
        current_time: datetime
    ) -> StrategySignal:
        """
        Generate alpha signal for momentum rank strategy (Phase 1).
        
        Alpha score calculation:
        - Based on multi-timeframe momentum score
        - Positive alpha indicates strong momentum
        - Higher score = stronger trend across timeframes
        
        Returns:
            StrategySignal with alpha_score, confidence, and metadata
        """
        latest = self.get_latest_features(features, current_time)
        
        if latest is None:
            return StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                alpha_score=0.0,
                confidence=0.0,
                horizon_days=self.default_horizon_days,
                volatility_adjusted=False,
                metadata={'error': 'no_data', 'strategy_name': self.name}
            )
        
        # Check if passes filters
        passes_filters = self._passes_filters(latest)
        
        # Calculate momentum score (can be negative for downtrends)
        momentum_score = self._calculate_momentum_score(latest)
        
        # Normalize momentum score to [-1, 1] range (already close to this)
        alpha_score = np.clip(momentum_score, -1.0, 1.0)
        
        # Only set positive alpha if passes filters
        if not passes_filters or alpha_score < self.parameters['min_momentum_score']:
            alpha_score = 0.0
        
        # Confidence based on momentum consistency
        confidence = self._calculate_confidence(latest, momentum_score)
        
        # Build metadata
        metadata = {
            'strategy_name': self.name,
            'momentum_score': float(momentum_score),
            'atr_pct': float(latest.get('atr_pct', 0)),
            'volume_zscore': float(latest.get('volume_zscore', 0)),
            'passes_filters': passes_filters,
        }
        
        # Add momentum components if available
        for col in ['price_momentum_1', 'price_momentum_5', 'price_momentum_10']:
            if col in latest.index:
                metadata[col] = float(latest[col])
        
        return StrategySignal(
            timestamp=current_time,
            symbol=symbol,
            alpha_score=alpha_score,
            confidence=confidence,
            horizon_days=self.default_horizon_days,
            volatility_adjusted=False,
            metadata=metadata
        )
    
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
        Exit conditions for momentum rank strategy.
        
        Close position when:
        1. Momentum score drops below threshold - trend weakening
        2. Volume dries up (z-score < -1) - low conviction
        3. Stop loss: down >2.5% from entry
        4. Take profit: up >5% from entry
        5. Maximum hold time: 6 hours (momentum trades are faster)
        """
        latest = self.get_latest_features(features, current_time)
        
        if latest is None:
            return True
        
        # Calculate current P&L
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Tighter stop loss for momentum strategy: -2.5%
        if pnl_pct < -2.5:
            return True
        
        # Take profit: +5%
        if pnl_pct > 5.0:
            return True
        
        # Momentum deterioration - exit if score drops significantly
        current_score = self._calculate_momentum_score(latest)
        if current_score < 0.1:  # Much weaker than entry requirement
            return True
        
        # Volume dries up - low conviction
        if 'volume_zscore' in latest.index and latest['volume_zscore'] < -1.0:
            return True
        
        # Volatility spike - risk management
        if 'atr_pct' in latest.index and latest['atr_pct'] > self.parameters['atr_pct_max'] * 1.5:
            return True
        
        # Maximum holding time: 6 hours (momentum strategies act faster)
        time_held = (current_time - entry_time).total_seconds() / 3600
        if time_held >= 6.0:
            return True
        
        return False
    
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
    
    def _calculate_confidence(self, row: pd.Series, momentum_score: float) -> float:
        """
        Calculate confidence in the momentum signal.
        
        Confidence factors:
        - Consistency across timeframes (all positive = more confident)
        - Volume confirmation (higher volume z-score = more confident)
        - Momentum strength (higher score = more confident)
        
        Returns:
            Confidence score from 0 to 1
        """
        # Base confidence on absolute momentum strength
        confidence = min(abs(momentum_score), 1.0)
        
        # Boost confidence if multiple timeframes agree
        positive_count = 0
        total_count = 0
        for col in ['price_momentum_1', 'price_momentum_5', 'price_momentum_10']:
            if col in row.index and not pd.isna(row[col]):
                total_count += 1
                if row[col] > 0:
                    positive_count += 1
        
        if total_count > 0:
            agreement = positive_count / total_count
            if agreement > 0.8:  # Strong agreement
                confidence = min(1.0, confidence * 1.15)
        
        # Boost confidence for strong volume
        volume_zscore = row.get('volume_zscore', 0)
        if volume_zscore > 0.5:
            confidence = min(1.0, confidence * 1.1)
        
        # Reduce confidence in high volatility
        atr_pct = row.get('atr_pct', 0)
        if atr_pct > 5.0:
            confidence *= 0.9
        
        return min(1.0, max(0.0, confidence))
