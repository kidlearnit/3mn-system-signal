"""
Strategy Configuration System - Flexible trading strategy management
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class StrategyType(Enum):
    MACD_ZONE = "macd_zone"
    TRINITY = "trinity"
    MOMENTUM = "momentum"
    STRUCTURE = "structure"
    CUSTOM = "custom"

@dataclass
class StrategyConfig:
    """Configuration for a trading strategy"""
    strategy_id: int
    name: str
    strategy_type: StrategyType
    description: str
    is_active: bool = True
    
    # Core components
    use_fmacd: bool = True
    use_smacd: bool = True
    use_bars_mt: bool = False
    use_3m2_structure: bool = False
    use_momentum_formula: bool = False
    
    # Timeframe weights (customizable per strategy)
    tf_weights: Dict[str, int] = None
    
    # Trinity requirements
    trinity_min_consensus: int = 2  # Minimum 2/3 for trinity
    
    # Cross-timeframe validation
    require_synchronization: bool = False
    sync_timeframes: List[str] = None
    
    # Custom parameters
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tf_weights is None:
            self.tf_weights = {
                '1D4hr': 6, '1D1hr': 5, '1D30Min': 4,
                '1D15Min': 3, '1D5Min': 2, '1D2Min': 1, '1D1Min': 1
            }
        
        if self.sync_timeframes is None:
            self.sync_timeframes = ['1D1Min', '1D2Min', '1D5Min']
        
        if self.custom_params is None:
            self.custom_params = {}

# Predefined strategy configurations
STRATEGY_CONFIGS = {
    1: StrategyConfig(
        strategy_id=1,
        name="MACD Zone Strategy",
        strategy_type=StrategyType.MACD_ZONE,
        description="Traditional MACD zone-based strategy",
        use_fmacd=True,
        use_smacd=True,
        use_bars_mt=False,
        use_3m2_structure=False,
        require_synchronization=False
    ),
    
    2: StrategyConfig(
        strategy_id=2,
        name="Trinity Strategy",
        strategy_type=StrategyType.TRINITY,
        description="Advanced trinity system with 3M2, FSMACD & Bars MT",
        use_fmacd=True,
        use_smacd=True,
        use_bars_mt=True,
        use_3m2_structure=True,
        use_momentum_formula=True,
        trinity_min_consensus=2,
        require_synchronization=True,
        sync_timeframes=['1D1Min', '1D2Min', '1D5Min'],
        tf_weights={
            '1D4hr': 8, '1D1hr': 7, '1D30Min': 6,
            '1D15Min': 5, '1D5Min': 4, '1D2Min': 3, '1D1Min': 2
        }
    ),
    
    3: StrategyConfig(
        strategy_id=3,
        name="Momentum Strategy",
        strategy_type=StrategyType.MOMENTUM,
        description="Momentum-based strategy focusing on MT calculations",
        use_fmacd=True,
        use_smacd=True,
        use_bars_mt=True,
        use_momentum_formula=True,
        require_synchronization=False,
        custom_params={
            'mt_threshold': 1.0,
            'focus_tf': '1D5Min'
        }
    ),
    
    4: StrategyConfig(
        strategy_id=4,
        name="Structure Strategy",
        strategy_type=StrategyType.STRUCTURE,
        description="Structure-focused strategy with 3M2 uniformity",
        use_fmacd=True,
        use_smacd=True,
        use_3m2_structure=True,
        require_synchronization=True,
        sync_timeframes=['1D1Min', '1D2Min', '1D5Min', '1D15Min'],
        custom_params={
            'structure_uniformity_threshold': 0.8
        }
    )
}

def get_strategy_config(strategy_id: int) -> Optional[StrategyConfig]:
    """Get strategy configuration by ID"""
    return STRATEGY_CONFIGS.get(strategy_id)

def get_strategy_for_symbol(symbol_id: int) -> Optional[StrategyConfig]:
    """Get strategy configuration for a specific symbol"""
    # This would query the database to get symbol's assigned strategy
    # For now, return default strategy
    return get_strategy_config(1)  # Default to MACD Zone

def create_custom_strategy(
    name: str,
    description: str,
    use_fmacd: bool = True,
    use_smacd: bool = True,
    use_bars_mt: bool = False,
    use_3m2_structure: bool = False,
    use_momentum_formula: bool = False,
    trinity_min_consensus: int = 2,
    require_synchronization: bool = False,
    sync_timeframes: List[str] = None,
    tf_weights: Dict[str, int] = None,
    custom_params: Dict[str, Any] = None
) -> StrategyConfig:
    """Create a custom strategy configuration"""
    strategy_id = max(STRATEGY_CONFIGS.keys()) + 1 if STRATEGY_CONFIGS else 1
    
    return StrategyConfig(
        strategy_id=strategy_id,
        name=name,
        strategy_type=StrategyType.CUSTOM,
        description=description,
        use_fmacd=use_fmacd,
        use_smacd=use_smacd,
        use_bars_mt=use_bars_mt,
        use_3m2_structure=use_3m2_structure,
        use_momentum_formula=use_momentum_formula,
        trinity_min_consensus=trinity_min_consensus,
        require_synchronization=require_synchronization,
        sync_timeframes=sync_timeframes,
        tf_weights=tf_weights,
        custom_params=custom_params or {}
    )

def list_available_strategies() -> List[StrategyConfig]:
    """List all available strategy configurations"""
    return list(STRATEGY_CONFIGS.values())

def update_strategy_config(strategy_id: int, **kwargs) -> bool:
    """Update strategy configuration"""
    if strategy_id not in STRATEGY_CONFIGS:
        return False
    
    config = STRATEGY_CONFIGS[strategy_id]
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return True
