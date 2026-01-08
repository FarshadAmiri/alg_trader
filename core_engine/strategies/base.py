"""
Base strategy interface.
"""
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class StrategySignal:
    """
    Standardized output from all strategies.
    
    Replaces simple buy/sell signals with rich alpha information
    that can be combined, weighted, and optimized.
    """
    timestamp: datetime
    symbol: str
    alpha_score: float        # -1 (strong sell) to +1 (strong buy), 0 = neutral
    confidence: float         # 0 to 1, how certain the strategy is
    horizon_days: int         # prediction timeframe (1, 5, 20, etc.)
    volatility_adjusted: bool = False  # whether alpha_score already accounts for volatility
    metadata: Dict[str, Any] = field(default_factory=dict)  # strategy-specific details
    
    def __post_init__(self):
        """Validate signal values."""
        if not -1.0 <= self.alpha_score <= 1.0:
            raise ValueError(f"alpha_score must be in [-1, 1], got {self.alpha_score}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")
        if self.horizon_days < 1:
            raise ValueError(f"horizon_days must be >= 1, got {self.horizon_days}")
    
    def to_legacy_signal(self) -> str:
        """Convert to legacy signal format for backward compatibility."""
        if self.alpha_score > 0.2:
            return "LONG"
        elif self.alpha_score < -0.2:
            return "SHORT"
        else:
            return "FLAT"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'alpha_score': self.alpha_score,
            'confidence': self.confidence,
            'horizon_days': self.horizon_days,
            'volatility_adjusted': self.volatility_adjusted,
            'metadata': self.metadata,
        }


class AlphaScoreNormalizer:
    """Utilities for normalizing alpha scores."""
    
    @staticmethod
    def zscore(values: pd.Series, clip: float = 3.0) -> pd.Series:
        """
        Convert values to z-scores and clip to [-1, 1].
        
        Args:
            values: Raw indicator values
            clip: Clip z-scores at +/- this value (default 3 sigma)
        
        Returns:
            Normalized scores in [-1, 1]
        """
        mean = values.mean()
        std = values.std()
        if std == 0:
            return pd.Series(0.0, index=values.index)
        
        zscores = (values - mean) / std
        clipped = np.clip(zscores, -clip, clip)
        normalized = clipped / clip  # Scale to [-1, 1]
        return normalized
    
    @staticmethod
    def minmax(values: pd.Series, lower_bound: float = None, 
              upper_bound: float = None) -> pd.Series:
        """
        Normalize values to [-1, 1] using min-max scaling.
        
        Args:
            values: Raw indicator values
            lower_bound: Optional fixed lower bound
            upper_bound: Optional fixed upper bound
        
        Returns:
            Normalized scores in [-1, 1]
        """
        vmin = lower_bound if lower_bound is not None else values.min()
        vmax = upper_bound if upper_bound is not None else values.max()
        
        if vmax == vmin:
            return pd.Series(0.0, index=values.index)
        
        # Scale to [0, 1] then to [-1, 1]
        normalized = 2 * (values - vmin) / (vmax - vmin) - 1
        return np.clip(normalized, -1, 1)
    
    @staticmethod
    def percentile_rank(values: pd.Series) -> pd.Series:
        """
        Convert values to percentile ranks, then to [-1, 1].
        
        Args:
            values: Raw indicator values
        
        Returns:
            Normalized scores in [-1, 1]
        """
        ranks = values.rank(pct=True)  # [0, 1]
        normalized = 2 * ranks - 1      # [-1, 1]
        return normalized


class TradingStrategy(ABC):
    """Base interface for trading strategies."""
    
    name: str = "base_strategy"
    
    # Strategy metadata (define in subclasses)
    preferred_timeframe: str = "5m"              # Optimal candle timeframe
    evaluation_mode: str = "periodic"            # "every_bar" or "periodic"
    evaluation_interval_hours: float = 2.0       # If periodic, check every N hours
    max_hold_hours: float = 4.0                  # Maximum position hold time
    typical_hold_range: str = "1-4 hours"        # Human-readable typical hold
    
    # Alpha signal metadata (new in Phase 1)
    default_horizon_days: int = 1                # Default prediction horizon
    requires_volatility_adjustment: bool = False  # If True, alpha_score needs vol scaling
    
    def __init__(self, parameters: Optional[Dict] = None):
        """
        Initialize strategy with parameters.
        
        Args:
            parameters: Dictionary of strategy-specific parameters
        """
        self.parameters = parameters or {}
        self.normalizer = AlphaScoreNormalizer()
    
    def generate_alpha_signal(
        self,
        symbol: str,
        features: pd.DataFrame,
        current_time: datetime
    ) -> StrategySignal:
        """
        Generate alpha signal for a specific symbol (new interface).
        
        This is the new preferred method that returns rich signal information.
        Strategies should implement this method to return alpha scores and confidence.
        
        Args:
            symbol: Symbol to evaluate
            features: DataFrame with computed features
            current_time: Current evaluation timestamp
        
        Returns:
            StrategySignal with alpha_score, confidence, and metadata
        """
        # Default implementation: convert legacy signal to alpha score
        # Subclasses should override this with proper alpha score calculation
        legacy_signal = self.generate_signal(symbol, features, current_time)
        
        if legacy_signal == "LONG":
            alpha_score = 0.5
            confidence = 0.5
        elif legacy_signal == "SHORT":
            alpha_score = -0.5
            confidence = 0.5
        else:  # FLAT
            alpha_score = 0.0
            confidence = 0.5
        
        return StrategySignal(
            timestamp=current_time,
            symbol=symbol,
            alpha_score=alpha_score,
            confidence=confidence,
            horizon_days=self.default_horizon_days,
            volatility_adjusted=False,
            metadata={'legacy_signal': legacy_signal}
        )
    
    @abstractmethod
    def select_symbols(
        self,
        features_by_symbol: Dict[str, pd.DataFrame],
        current_time: datetime
    ) -> List[str]:
        """
        Select symbols to trade at current time.
        
        Args:
            features_by_symbol: Dict mapping symbol -> DataFrame with features
            current_time: Current evaluation timestamp
        
        Returns:
            List of selected symbols (ranked by preference)
        """
        pass
    
    @abstractmethod
    def generate_signal(
        self,
        symbol: str,
        features: pd.DataFrame,
        current_time: datetime
    ) -> str:
        """
        Generate trading signal for a specific symbol.
        
        Args:
            symbol: Symbol to evaluate
            features: DataFrame with computed features
            current_time: Current evaluation timestamp
        
        Returns:
            "LONG", "SHORT", or "FLAT"
        """
        pass
    
    @abstractmethod
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
        Determine if an open position should be closed.
        
        This allows each strategy to define its own exit logic based on:
        - Technical indicators (e.g., RSI overbought, MACD crossover)
        - Profit targets or stop losses
        - Time-based exits (if desired)
        - Market conditions
        
        Args:
            symbol: Symbol of the open position
            features: DataFrame with computed features
            entry_time: When the position was entered
            current_time: Current evaluation timestamp
            entry_price: Price at entry
            current_price: Current market price
        
        Returns:
            True if position should be closed, False otherwise
        """
        pass
    
    def get_latest_features(
        self,
        features: pd.DataFrame,
        current_time: datetime
    ) -> Optional[pd.Series]:
        """
        Get the latest feature row at or before current_time.
        
        Args:
            features: DataFrame with features
            current_time: Current evaluation timestamp
        
        Returns:
            Latest feature row as Series, or None if not available
        """
        if features.empty:
            return None
        
        # Ensure timestamp column exists
        if 'timestamp' not in features.columns:
            return None
        
        # Filter to data at or before current_time
        valid_data = features[features['timestamp'] <= current_time]
        
        if valid_data.empty:
            return None
        
        # Return the last row
        return valid_data.iloc[-1]
