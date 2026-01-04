"""
Risk management rules and filters.
"""
import pandas as pd
from typing import List, Dict, Optional


class RiskManager:
    """Apply risk filters to trading decisions."""
    
    def __init__(
        self,
        max_positions: int = 3,
        max_volatility_pct: float = 5.0,
        min_volume_ratio: float = 0.5
    ):
        self.max_positions = max_positions
        self.max_volatility_pct = max_volatility_pct
        self.min_volume_ratio = min_volume_ratio
    
    def allow_symbol(self, features: pd.Series) -> bool:
        """
        Check if a symbol passes risk filters.
        
        Args:
            features: Latest feature row for the symbol
        
        Returns:
            True if symbol is allowed, False otherwise
        """
        # Volatility check
        if 'atr_pct' in features.index:
            if features['atr_pct'] > self.max_volatility_pct:
                return False
        
        # Volume check
        if 'volume_ratio' in features.index:
            if features['volume_ratio'] < self.min_volume_ratio:
                return False
        
        # Price sanity checks
        if 'close' in features.index:
            if features['close'] <= 0:
                return False
        
        return True
    
    def filter_symbols(
        self,
        symbols: List[str],
        features_by_symbol: Dict[str, pd.DataFrame]
    ) -> List[str]:
        """
        Filter list of symbols based on risk rules.
        
        Args:
            symbols: List of candidate symbols
            features_by_symbol: Features for each symbol
        
        Returns:
            Filtered list of symbols
        """
        allowed = []
        
        for symbol in symbols:
            if symbol not in features_by_symbol:
                continue
            
            features = features_by_symbol[symbol]
            if features.empty:
                continue
            
            latest = features.iloc[-1]
            
            if self.allow_symbol(latest):
                allowed.append(symbol)
        
        # Enforce max positions
        return allowed[:self.max_positions]


class Allocator:
    """Determine position allocations."""
    
    def __init__(self, allocation_method: str = 'equal'):
        """
        Initialize allocator.
        
        Args:
            allocation_method: 'equal', 'risk_parity', or 'score_weighted'
        """
        self.allocation_method = allocation_method
    
    def allocate(
        self,
        symbols: List[str],
        features_by_symbol: Optional[Dict[str, pd.DataFrame]] = None,
        scores: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Allocate capital weights to symbols.
        
        Args:
            symbols: List of symbols to allocate
            features_by_symbol: Optional features for risk-based allocation
            scores: Optional scores for weighted allocation
        
        Returns:
            Dictionary mapping symbol -> weight (sum = 1.0)
        """
        if not symbols:
            return {}
        
        if self.allocation_method == 'equal':
            return self._equal_weight(symbols)
        elif self.allocation_method == 'risk_parity' and features_by_symbol:
            return self._risk_parity(symbols, features_by_symbol)
        elif self.allocation_method == 'score_weighted' and scores:
            return self._score_weighted(symbols, scores)
        else:
            # Default to equal weight
            return self._equal_weight(symbols)
    
    def _equal_weight(self, symbols: List[str]) -> Dict[str, float]:
        """Equal weight allocation."""
        n = len(symbols)
        weight = 1.0 / n
        return {symbol: weight for symbol in symbols}
    
    def _risk_parity(
        self,
        symbols: List[str],
        features_by_symbol: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """
        Risk parity allocation (inverse volatility weighting).
        """
        volatilities = {}
        
        for symbol in symbols:
            if symbol in features_by_symbol:
                features = features_by_symbol[symbol]
                if not features.empty and 'atr_pct' in features.columns:
                    vol = features.iloc[-1]['atr_pct']
                    volatilities[symbol] = max(vol, 0.1)  # Avoid division by zero
                else:
                    volatilities[symbol] = 1.0
            else:
                volatilities[symbol] = 1.0
        
        # Inverse volatility weights
        inv_vols = {s: 1.0 / v for s, v in volatilities.items()}
        total = sum(inv_vols.values())
        
        return {s: w / total for s, w in inv_vols.items()}
    
    def _score_weighted(
        self,
        symbols: List[str],
        scores: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Score-weighted allocation.
        """
        total_score = sum(scores.get(s, 0) for s in symbols)
        
        if total_score == 0:
            return self._equal_weight(symbols)
        
        return {s: scores.get(s, 0) / total_score for s in symbols}
