"""
Strategy and feature registry.
"""
from typing import Dict, Type, Optional
import importlib


class StrategyRegistry:
    """Registry for trading strategies."""
    
    _strategies: Dict[str, Type] = {}
    
    @classmethod
    def register(cls, name: str, strategy_class: Type):
        """Register a strategy class."""
        cls._strategies[name] = strategy_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type]:
        """Get a strategy class by name."""
        return cls._strategies.get(name)
    
    @classmethod
    def list_all(cls) -> Dict[str, Type]:
        """List all registered strategies."""
        return cls._strategies.copy()
    
    @classmethod
    def load_from_path(cls, module_path: str):
        """
        Load strategy from module path.
        
        Args:
            module_path: e.g., "core_engine.strategies.macd_rsi_confluence:MACDRSIStrategy"
        
        Returns:
            Strategy class
        """
        try:
            module_name, class_name = module_path.split(':')
            module = importlib.import_module(module_name)
            strategy_class = getattr(module, class_name)
            return strategy_class
        except Exception as e:
            raise ImportError(f"Failed to load strategy from {module_path}: {e}")


class FeatureRegistry:
    """Registry for feature computers."""
    
    _features: Dict[str, Type] = {}
    
    @classmethod
    def register(cls, name: str, feature_class: Type):
        """Register a feature computer class."""
        cls._features[name] = feature_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type]:
        """Get a feature computer class by name."""
        return cls._features.get(name)
    
    @classmethod
    def list_all(cls) -> Dict[str, Type]:
        """List all registered feature computers."""
        return cls._features.copy()


# Auto-register built-in strategies
def register_builtin_strategies():
    """Register all built-in strategies."""
    from core_engine.strategies.macd_rsi_confluence import MACDRSIStrategy
    from core_engine.strategies.momentum_rank import MomentumRankStrategy
    
    StrategyRegistry.register('macd_rsi_confluence', MACDRSIStrategy)
    StrategyRegistry.register('momentum_rank', MomentumRankStrategy)


# Auto-register built-in features
def register_builtin_features():
    """Register all built-in feature computers."""
    from core_engine.features.momentum import MomentumFeatures, TrendFeatures
    from core_engine.features.volatility import VolatilityFeatures, RangeFeatures
    from core_engine.features.liquidity import LiquidityFeatures, CompositeFeatures
    
    FeatureRegistry.register('momentum', MomentumFeatures)
    FeatureRegistry.register('trend', TrendFeatures)
    FeatureRegistry.register('volatility', VolatilityFeatures)
    FeatureRegistry.register('range', RangeFeatures)
    FeatureRegistry.register('liquidity', LiquidityFeatures)
    FeatureRegistry.register('composite', CompositeFeatures)


# Initialize registries on import
try:
    register_builtin_strategies()
    register_builtin_features()
except Exception:
    pass  # Ignore errors during initial setup
