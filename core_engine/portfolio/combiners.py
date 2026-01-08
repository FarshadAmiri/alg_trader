"""
Signal combination methods for portfolio management.

Combines signals from multiple strategies into a single alpha score per asset.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict
from core_engine.strategies.base import StrategySignal


class SignalCombiner:
    """Combines signals from multiple strategies."""
    
    def __init__(self, method: str = 'weighted', strategy_weights: Dict[str, float] = None):
        """
        Initialize signal combiner.
        
        Args:
            method: Combination method ('weighted', 'confidence_weighted', 'rank_average', 'best_strategy')
            strategy_weights: Optional dict mapping strategy_name -> weight (for 'weighted' method)
        """
        self.method = method
        self.strategy_weights = strategy_weights or {}
    
    def combine(self, signals: List[StrategySignal]) -> Dict[str, Tuple[float, float]]:
        """
        Combine multiple strategy signals into single alpha per asset.
        
        Args:
            signals: List of StrategySignal objects from multiple strategies
        
        Returns:
            Dict mapping symbol -> (combined_alpha, combined_confidence)
        """
        if not signals:
            return {}
        
        # Group signals by symbol
        signals_by_symbol = defaultdict(list)
        for signal in signals:
            signals_by_symbol[signal.symbol].append(signal)
        
        # Combine signals for each symbol
        combined = {}
        for symbol, symbol_signals in signals_by_symbol.items():
            if self.method == 'weighted':
                alpha, conf = self._weighted_average(symbol_signals)
            elif self.method == 'confidence_weighted':
                alpha, conf = self._confidence_weighted(symbol_signals)
            elif self.method == 'rank_average':
                alpha, conf = self._rank_average(symbol_signals)
            elif self.method == 'best_strategy':
                alpha, conf = self._best_strategy(symbol_signals)
            else:
                raise ValueError(f"Unknown combination method: {self.method}")
            
            combined[symbol] = (alpha, conf)
        
        return combined
    
    def _weighted_average(self, signals: List[StrategySignal]) -> Tuple[float, float]:
        """Weighted average of alpha scores."""
        total_weight = 0.0
        weighted_alpha = 0.0
        weighted_conf = 0.0
        
        for signal in signals:
            # Get strategy weight (default to equal weights)
            strategy_name = signal.metadata.get('strategy_name', 'unknown')
            weight = self.strategy_weights.get(strategy_name, 1.0)
            
            weighted_alpha += signal.alpha_score * weight
            weighted_conf += signal.confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0, 0.0
        
        return weighted_alpha / total_weight, weighted_conf / total_weight
    
    def _confidence_weighted(self, signals: List[StrategySignal]) -> Tuple[float, float]:
        """Weight signals by their confidence levels."""
        total_conf = sum(s.confidence for s in signals)
        
        if total_conf == 0:
            return 0.0, 0.0
        
        combined_alpha = sum(s.alpha_score * s.confidence for s in signals) / total_conf
        combined_conf = total_conf / len(signals)  # Average confidence
        
        return combined_alpha, combined_conf
    
    def _rank_average(self, signals: List[StrategySignal]) -> Tuple[float, float]:
        """
        Average of strategy ranks (more robust to outliers).
        
        Note: This method needs all symbols to rank properly.
        For now, just average the alpha scores.
        """
        avg_alpha = np.mean([s.alpha_score for s in signals])
        avg_conf = np.mean([s.confidence for s in signals])
        
        return float(avg_alpha), float(avg_conf)
    
    def _best_strategy(self, signals: List[StrategySignal]) -> Tuple[float, float]:
        """Use signal from highest-confidence strategy."""
        best_signal = max(signals, key=lambda s: s.confidence)
        return best_signal.alpha_score, best_signal.confidence
    
    def get_available_methods(self) -> List[str]:
        """Return list of available combination methods."""
        return ['weighted', 'confidence_weighted', 'rank_average', 'best_strategy']
