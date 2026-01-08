"""
Portfolio Manager - Main interface for combining strategies and managing allocations.

This is the central component that orchestrates signal combination and capital allocation.
"""
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from core_engine.strategies.base import TradingStrategy, StrategySignal
from .combiners import SignalCombiner
from .allocators import CapitalAllocator


class PortfolioManager:
    """
    Manages a portfolio of multiple trading strategies.
    
    Responsibilities:
    - Combine signals from multiple strategies
    - Rank assets based on combined alpha scores
    - Allocate capital across positions
    - Handle conflicts between strategies
    - Apply portfolio constraints
    """
    
    def __init__(
        self,
        strategies: List[TradingStrategy],
        combination_method: str = 'weighted',
        allocation_method: str = 'proportional',
        strategy_weights: Optional[Dict[str, float]] = None,
        total_capital: float = 100000.0
    ):
        """
        Initialize portfolio manager.
        
        Args:
            strategies: List of TradingStrategy instances
            combination_method: How to combine signals ('weighted', 'confidence_weighted', etc.)
            allocation_method: How to allocate capital ('proportional', 'equal_weight', etc.)
            strategy_weights: Optional dict mapping strategy_name -> weight
            total_capital: Total capital to manage
        """
        self.strategies = strategies
        self.combination_method = combination_method
        self.allocation_method = allocation_method
        self.total_capital = total_capital
        
        # Initialize combiner and allocator
        self.combiner = SignalCombiner(
            method=combination_method,
            strategy_weights=strategy_weights or {}
        )
        self.allocator = CapitalAllocator(
            method=allocation_method,
            total_capital=total_capital
        )
    
    def generate_portfolio_signals(
        self,
        features_by_symbol: Dict[str, pd.DataFrame],
        current_time: datetime
    ) -> Dict[str, StrategySignal]:
        """
        Generate signals from all strategies and combine them.
        
        Args:
            features_by_symbol: Dict mapping symbol -> DataFrame with features
            current_time: Current evaluation timestamp
        
        Returns:
            Dict mapping symbol -> StrategySignal (with combined alpha)
        """
        all_signals = []
        
        # Collect signals from all strategies
        for strategy in self.strategies:
            print(f"[PORTFOLIO MGR] Processing strategy: {strategy.name}")
            
            # Each strategy selects its preferred symbols
            try:
                selected_symbols = strategy.select_symbols(features_by_symbol, current_time)
                print(f"[PORTFOLIO MGR] {strategy.name} selected {len(selected_symbols)} symbols")
            except Exception as e:
                print(f"[PORTFOLIO MGR] ERROR in {strategy.name}.select_symbols: {e}")
                continue
            
            # Generate alpha signals for selected symbols
            for symbol in selected_symbols:
                if symbol not in features_by_symbol:
                    continue
                
                try:
                    features = features_by_symbol[symbol]
                    signal = strategy.generate_alpha_signal(symbol, features, current_time)
                    
                    # Add strategy name to metadata
                    signal.metadata['strategy_name'] = strategy.name
                    all_signals.append(signal)
                except Exception as e:
                    print(f"[PORTFOLIO MGR] ERROR generating signal for {symbol} with {strategy.name}: {e}")
                    continue
        
        print(f"[PORTFOLIO MGR] Collected {len(all_signals)} signals from {len(self.strategies)} strategies")
        
        # Combine signals
        combined_alphas = self.combiner.combine(all_signals)
        
        # Convert back to StrategySignal objects
        combined_signals = {}
        for symbol, (alpha, confidence) in combined_alphas.items():
            combined_signals[symbol] = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                alpha_score=alpha,
                confidence=confidence,
                horizon_days=1,  # Use shortest horizon for portfolio
                volatility_adjusted=False,
                metadata={
                    'combination_method': self.combination_method,
                    'num_strategies': len([s for s in all_signals if s.symbol == symbol])
                }
            )
        
        return combined_signals
    
    def allocate_capital(
        self,
        combined_signals: Dict[str, StrategySignal],
        constraints: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Allocate capital based on combined signals.
        
        Args:
            combined_signals: Dict mapping symbol -> StrategySignal
            constraints: Optional constraints for allocation
        
        Returns:
            Dict mapping symbol -> dollar allocation
        """
        # Convert signals to (alpha, confidence) tuples
        combined_alphas = {
            symbol: (signal.alpha_score, signal.confidence)
            for symbol, signal in combined_signals.items()
        }
        
        # Allocate capital
        allocations = self.allocator.allocate(combined_alphas, constraints)
        
        return allocations
    
    def get_portfolio_positions(
        self,
        features_by_symbol: Dict[str, pd.DataFrame],
        current_time: datetime,
        constraints: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Get complete portfolio positions with allocations.
        
        Args:
            features_by_symbol: Dict mapping symbol -> DataFrame with features
            current_time: Current evaluation timestamp
            constraints: Optional constraints for allocation
        
        Returns:
            DataFrame with columns: symbol, alpha_score, confidence, allocation, weight
        """
        # Generate combined signals
        combined_signals = self.generate_portfolio_signals(features_by_symbol, current_time)
        
        # Allocate capital
        allocations = self.allocate_capital(combined_signals, constraints)
        
        # Build results DataFrame
        positions = []
        for symbol, allocation in allocations.items():
            signal = combined_signals.get(symbol)
            if signal:
                positions.append({
                    'symbol': symbol,
                    'alpha_score': signal.alpha_score,
                    'confidence': signal.confidence,
                    'allocation': allocation,
                    'weight': allocation / self.total_capital,
                    'num_strategies': signal.metadata.get('num_strategies', 0)
                })
        
        df = pd.DataFrame(positions)
        
        if not df.empty:
            df = df.sort_values('allocation', ascending=False)
        
        return df
    
    def update_strategy_weights(self, strategy_weights: Dict[str, float]):
        """
        Update strategy weights for signal combination.
        
        Args:
            strategy_weights: Dict mapping strategy_name -> weight
        """
        self.combiner.strategy_weights = strategy_weights
    
    def set_combination_method(self, method: str):
        """Change the signal combination method."""
        self.combiner.method = method
        self.combination_method = method
    
    def set_allocation_method(self, method: str):
        """Change the capital allocation method."""
        self.allocator.method = method
        self.allocation_method = method
    
    def get_available_methods(self) -> Dict[str, List[str]]:
        """Get available combination and allocation methods."""
        return {
            'combination': self.combiner.get_available_methods(),
            'allocation': self.allocator.get_available_methods()
        }
