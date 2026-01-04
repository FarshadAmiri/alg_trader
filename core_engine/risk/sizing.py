"""
Position sizing utilities (for future v2 with capital compounding).
"""
from typing import Optional


class PositionSizer:
    """Calculate position sizes based on risk parameters."""
    
    def __init__(
        self,
        account_size: float,
        risk_per_trade_pct: float = 2.0,
        max_position_size_pct: float = 20.0
    ):
        """
        Initialize position sizer.
        
        Args:
            account_size: Total account capital
            risk_per_trade_pct: Max % of capital to risk per trade
            max_position_size_pct: Max % of capital per position
        """
        self.account_size = account_size
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_position_size_pct = max_position_size_pct
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float,
        atr: Optional[float] = None
    ) -> float:
        """
        Calculate position size based on risk.
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            atr: Average True Range (optional, for dynamic stops)
        
        Returns:
            Position size in quote currency
        """
        if entry_price <= 0 or stop_loss_price <= 0:
            return 0.0
        
        # Risk amount in currency
        risk_amount = self.account_size * (self.risk_per_trade_pct / 100)
        
        # Risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        if risk_per_unit == 0:
            return 0.0
        
        # Position size
        position_size = risk_amount / risk_per_unit
        
        # Apply max position size constraint
        max_position = self.account_size * (self.max_position_size_pct / 100)
        position_size = min(position_size, max_position)
        
        return position_size
    
    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        atr_multiplier: float = 2.0
    ) -> float:
        """
        Calculate ATR-based stop loss.
        
        Args:
            entry_price: Entry price
            atr: Average True Range
            atr_multiplier: Multiplier for ATR
        
        Returns:
            Stop loss price
        """
        stop_distance = atr * atr_multiplier
        return entry_price - stop_distance
