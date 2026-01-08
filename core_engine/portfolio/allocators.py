"""
Capital allocation methods for portfolio construction.

Converts alpha scores into position sizes and capital allocations.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional


class CapitalAllocator:
    """Allocates capital to assets based on alpha scores."""
    
    def __init__(self, method: str = 'proportional', total_capital: float = 100000.0):
        """
        Initialize capital allocator.
        
        Args:
            method: Allocation method ('proportional', 'equal_weight', 'top_n', 'threshold')
            total_capital: Total capital to allocate
        """
        self.method = method
        self.total_capital = total_capital
    
    def allocate(
        self,
        combined_alphas: Dict[str, Tuple[float, float]],
        constraints: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Allocate capital to assets based on combined alpha scores.
        
        Args:
            combined_alphas: Dict mapping symbol -> (alpha_score, confidence)
            constraints: Optional constraints dict with:
                - max_position_pct: Maximum % of portfolio per position (default 20%)
                - min_position_pct: Minimum % of portfolio per position (default 1%)
                - max_positions: Maximum number of positions (default no limit)
                - min_alpha_threshold: Minimum alpha score to allocate (default 0.1)
        
        Returns:
            Dict mapping symbol -> dollar allocation
        """
        constraints = constraints or {}
        max_position_pct = constraints.get('max_position_pct', 0.20)
        min_position_pct = constraints.get('min_position_pct', 0.01)
        max_positions = constraints.get('max_positions', None)
        min_alpha_threshold = constraints.get('min_alpha_threshold', 0.1)
        
        # Filter symbols below threshold
        filtered_alphas = {
            symbol: (alpha, conf)
            for symbol, (alpha, conf) in combined_alphas.items()
            if abs(alpha) >= min_alpha_threshold
        }
        
        if not filtered_alphas:
            return {}
        
        # Allocate based on method
        if self.method == 'proportional':
            allocations = self._proportional_allocation(filtered_alphas)
        elif self.method == 'equal_weight':
            allocations = self._equal_weight_allocation(filtered_alphas)
        elif self.method == 'top_n':
            n = constraints.get('top_n', 10)
            allocations = self._top_n_allocation(filtered_alphas, n)
        elif self.method == 'threshold':
            allocations = self._threshold_allocation(filtered_alphas)
        else:
            raise ValueError(f"Unknown allocation method: {self.method}")
        
        # Apply position size constraints
        allocations = self._apply_constraints(
            allocations,
            max_position_pct,
            min_position_pct,
            max_positions
        )
        
        return allocations
    
    def _proportional_allocation(self, alphas: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
        """
        Allocate capital proportional to alpha scores.
        
        Positive alpha = long position, negative alpha = short position (if supported).
        """
        # For now, only allocate to positive alphas (long-only portfolio)
        long_alphas = {s: a for s, (a, c) in alphas.items() if a > 0}
        
        if not long_alphas:
            return {}
        
        total_alpha = sum(long_alphas.values())
        
        if total_alpha == 0:
            return {}
        
        # Allocate proportionally
        allocations = {
            symbol: (alpha / total_alpha) * self.total_capital
            for symbol, alpha in long_alphas.items()
        }
        
        return allocations
    
    def _equal_weight_allocation(self, alphas: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
        """Equal weight allocation to all positive alpha signals."""
        long_symbols = [s for s, (a, c) in alphas.items() if a > 0]
        
        if not long_symbols:
            return {}
        
        allocation_per_symbol = self.total_capital / len(long_symbols)
        
        return {symbol: allocation_per_symbol for symbol in long_symbols}
    
    def _top_n_allocation(self, alphas: Dict[str, Tuple[float, float]], n: int) -> Dict[str, float]:
        """Equal weight allocation to top N symbols by alpha score."""
        # Sort by alpha score
        sorted_symbols = sorted(alphas.items(), key=lambda x: abs(x[1][0]), reverse=True)
        
        # Take top N
        top_symbols = [s for s, (a, c) in sorted_symbols[:n] if a > 0]
        
        if not top_symbols:
            return {}
        
        allocation_per_symbol = self.total_capital / len(top_symbols)
        
        return {symbol: allocation_per_symbol for symbol in top_symbols}
    
    def _threshold_allocation(self, alphas: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
        """
        Allocate in tiers based on alpha score magnitude.
        
        High conviction (alpha > 0.5): 2x weight
        Medium conviction (0.3 < alpha <= 0.5): 1.5x weight
        Low conviction (alpha <= 0.3): 1x weight
        """
        tiers = {'high': [], 'medium': [], 'low': []}
        
        for symbol, (alpha, conf) in alphas.items():
            if alpha <= 0:
                continue
            
            if alpha > 0.5:
                tiers['high'].append(symbol)
            elif alpha > 0.3:
                tiers['medium'].append(symbol)
            else:
                tiers['low'].append(symbol)
        
        # Calculate total weight units
        total_units = (
            len(tiers['high']) * 2.0 +
            len(tiers['medium']) * 1.5 +
            len(tiers['low']) * 1.0
        )
        
        if total_units == 0:
            return {}
        
        unit_value = self.total_capital / total_units
        
        allocations = {}
        for symbol in tiers['high']:
            allocations[symbol] = unit_value * 2.0
        for symbol in tiers['medium']:
            allocations[symbol] = unit_value * 1.5
        for symbol in tiers['low']:
            allocations[symbol] = unit_value * 1.0
        
        return allocations
    
    def _apply_constraints(
        self,
        allocations: Dict[str, float],
        max_position_pct: float,
        min_position_pct: float,
        max_positions: Optional[int]
    ) -> Dict[str, float]:
        """Apply position size and count constraints."""
        if not allocations:
            return {}
        
        max_position_value = self.total_capital * max_position_pct
        min_position_value = self.total_capital * min_position_pct
        
        # Clip positions to max size
        constrained = {}
        for symbol, allocation in allocations.items():
            if allocation < min_position_value:
                continue  # Skip positions below minimum
            
            constrained[symbol] = min(allocation, max_position_value)
        
        # Limit number of positions if specified
        if max_positions and len(constrained) > max_positions:
            # Keep top N by allocation size
            sorted_positions = sorted(constrained.items(), key=lambda x: x[1], reverse=True)
            constrained = dict(sorted_positions[:max_positions])
        
        # Renormalize to use full capital
        total_allocated = sum(constrained.values())
        if total_allocated > 0 and total_allocated != self.total_capital:
            scale_factor = self.total_capital / total_allocated
            constrained = {s: v * scale_factor for s, v in constrained.items()}
        
        return constrained
    
    def get_available_methods(self) -> list:
        """Return list of available allocation methods."""
        return ['proportional', 'equal_weight', 'top_n', 'threshold']
