"""
Strategy Configuration Repository
Handles loading and caching of strategy configurations from workflows, DB, and environment.
"""

# StrategyConfigRepository doesn't need to inherit from BaseRepository
# as it's a specialized configuration repository
from app.db import SessionLocal, init_db
from sqlalchemy import text
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Initialize DB session if not already done
if SessionLocal is None:
    init_db(os.getenv("DATABASE_URL"))

class StrategyConfigRepository:
    """
    Repository for accessing and managing strategy configurations.
    Handles loading from workflows, DB, and environment with caching.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache_ttl = config.get('config_cache_ttl', 60)  # 1 minute cache
        self.default_tf_list = config.get('default_tf_list', ['2m', '5m', '15m', '30m', '1h'])
        self.default_min_consensus = config.get('default_min_consensus', 3)
        self.default_threshold = config.get('default_threshold', 0.33)
        self.default_macd_params = config.get('default_macd_params', {
            'fastPeriod': 7,
            'slowPeriod': 72,
            'signalPeriod': 144
        })
        # Simple cache implementation
        self._cache = {}
        self._cache_timestamps = {}
        logger.info(f"StrategyConfigRepository initialized with cache_ttl={self.cache_ttl}")

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self._cache and key in self._cache_timestamps:
            if (datetime.now() - self._cache_timestamps[key]).seconds < self.cache_ttl:
                return self._cache[key]
            else:
                # Expired, remove from cache
                del self._cache[key]
                del self._cache_timestamps[key]
        return None

    def _set_to_cache(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with timestamp"""
        self._cache[key] = value
        self._cache_timestamps[key] = datetime.now()

    def _invalidate_cache(self, key: str):
        """Remove key from cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._cache_timestamps:
            del self._cache_timestamps[key]

    def _generate_cache_key(self, operation: str, **kwargs) -> str:
        """Generate a cache key"""
        sorted_items = sorted(kwargs.items())
        params_str = "_".join(f"{k}={v}" for k, v in sorted_items)
        return f"{operation}|{params_str}"

    def get_macd_config(self, symbol: str) -> Dict[str, Any]:
        """
        Get MACD configuration for a symbol from workflows, with fallbacks.
        Returns a complete config dict with all required parameters.
        """
        cache_key = self._generate_cache_key("macd_config", symbol=symbol)
        cached_config = self._get_from_cache(cache_key)
        if cached_config:
            return cached_config

        # Try to get from workflows first
        workflow_config = self._get_workflow_config(symbol)
        if workflow_config:
            config = self._merge_with_defaults(workflow_config)
            self._set_to_cache(cache_key, config, ttl=self.cache_ttl)
            return config

        # Fallback to environment and defaults
        config = self._get_default_config()
        self._set_to_cache(cache_key, config, ttl=self.cache_ttl)
        return config

    def _get_workflow_config(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get MACD configuration from active workflows, prioritizing '25symbols'.
        """
        try:
            with SessionLocal() as s:
                rows = s.execute(text("""
                    SELECT name, nodes, properties FROM workflows
                    WHERE status='active' AND JSON_SEARCH(nodes, 'one', 'macd-multi') IS NOT NULL
                """)).fetchall()

            # Prioritize '25symbols' workflow
            preferred = [r for r in rows if (r[0] or '').strip().lower() == '25symbols']
            ordered = preferred + [r for r in rows if r not in preferred]

            for name, nodes_json, props_json in ordered:
                try:
                    nodes = json.loads(nodes_json)
                    props = json.loads(props_json)
                    macd_nodes = [n for n in nodes if n.get('type') == 'macd-multi']
                    
                    for node in macd_nodes:
                        cfg = props.get(node['id'], {})
                        for sc in cfg.get('symbolThresholds', []):
                            if isinstance(sc, dict) and sc.get('symbol', '').upper() == symbol.upper():
                                merged = dict(cfg)
                                merged.update(sc)
                                merged['__workflow_name'] = name
                                logger.debug(f"Found workflow config for {symbol} in {name}")
                                return merged
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Error parsing workflow {name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting workflow config for {symbol}: {e}")
            
        return None

    def _merge_with_defaults(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge workflow config with defaults to ensure all required fields are present.
        """
        config = dict(self.default_macd_params)
        config.update({
            'tf_list': self.default_tf_list,
            'min_consensus': self.default_min_consensus,
            'default_threshold': self.default_threshold
        })
        
        # Override with workflow values
        config.update(workflow_config)
        
        # Ensure tf_list is a list
        if isinstance(config.get('tf_list'), str):
            config['tf_list'] = [tf.strip() for tf in config['tf_list'].split(',')]
        
        # Ensure numeric values are properly typed
        for key in ['fastPeriod', 'slowPeriod', 'signalPeriod', 'min_consensus']:
            if key in config:
                try:
                    config[key] = int(config[key])
                except (ValueError, TypeError):
                    config[key] = self.default_macd_params.get(key, 0)
        
        # Ensure threshold values are floats
        threshold_keys = ['bubefsm1', 'bubefsm2', 'bubefsm5', 'bubefsm15', 'bubefsm30', 'bubefs_1h']
        for key in threshold_keys:
            if key in config:
                try:
                    config[key] = float(config[key])
                except (ValueError, TypeError):
                    config[key] = self.default_threshold
        
        return config

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration from environment and hardcoded defaults.
        """
        config = dict(self.default_macd_params)
        config.update({
            'tf_list': self.default_tf_list,
            'min_consensus': self.default_min_consensus,
            'default_threshold': self.default_threshold
        })
        
        # Override with environment variables if available
        env_overrides = {
            'fastPeriod': os.getenv('MACD_FAST_PERIOD'),
            'slowPeriod': os.getenv('MACD_SLOW_PERIOD'),
            'signalPeriod': os.getenv('MACD_SIGNAL_PERIOD'),
            'min_consensus': os.getenv('MACD_MIN_CONSENSUS'),
            'default_threshold': os.getenv('MACD_DEFAULT_THRESHOLD')
        }
        
        for key, value in env_overrides.items():
            if value:
                try:
                    if key == 'min_consensus':
                        config[key] = int(value)
                    else:
                        config[key] = float(value)
                except (ValueError, TypeError):
                    pass
        
        return config

    def get_tf_threshold(self, symbol: str, timeframe: str) -> float:
        """
        Get threshold for a specific timeframe from symbol's configuration.
        """
        config = self.get_macd_config(symbol)
        
        # Map timeframe to config key
        key_map = {
            '1m': 'bubefsm1',
            '2m': 'bubefsm2', 
            '5m': 'bubefsm5',
            '15m': 'bubefsm15',
            '30m': 'bubefsm30',
            '1h': 'bubefs_1h'
        }
        
        key = key_map.get(timeframe)
        if key and key in config:
            return float(config[key])
        
        return config.get('default_threshold', self.default_threshold)

    def get_symbol_exchange(self, symbol: str) -> str:
        """
        Get exchange for a symbol from workflow config or infer from symbol.
        """
        config = self.get_macd_config(symbol)
        
        # Check if exchange is explicitly set
        if 'exchange' in config and config['exchange']:
            return config['exchange'].upper()
        
        # Check sector
        if 'sector' in config and config['sector']:
            if config['sector'].upper() == 'VN':
                return 'HOSE'
        
        # Infer from symbol suffix
        if symbol.upper().endswith('.VN'):
            return 'HOSE'
        
        # Default to NASDAQ
        return 'NASDAQ'

    def is_symbol_active(self, symbol: str) -> bool:
        """
        Check if symbol is active in workflow configuration.
        """
        config = self.get_macd_config(symbol)
        return config.get('active', True)  # Default to active if not specified

    def get_all_active_symbols(self) -> List[Dict[str, Any]]:
        """
        Get all active symbols with their configurations.
        """
        cache_key = self._generate_cache_key("all_active_symbols")
        cached_symbols = self._get_from_cache(cache_key)
        if cached_symbols:
            return cached_symbols

        symbols = []
        try:
            with SessionLocal() as s:
                rows = s.execute(text("""
                    SELECT name, nodes, properties FROM workflows
                    WHERE status='active' AND JSON_SEARCH(nodes, 'one', 'macd-multi') IS NOT NULL
                """)).fetchall()

            for name, nodes_json, props_json in rows:
                try:
                    nodes = json.loads(nodes_json)
                    props = json.loads(props_json)
                    macd_nodes = [n for n in nodes if n.get('type') == 'macd-multi']
                    
                    for node in macd_nodes:
                        cfg = props.get(node['id'], {})
                        for sc in cfg.get('symbolThresholds', []):
                            if isinstance(sc, dict) and sc.get('symbol'):
                                symbol = sc['symbol']
                                if self.is_symbol_active(symbol):
                                    symbols.append({
                                        'symbol': symbol,
                                        'exchange': self.get_symbol_exchange(symbol),
                                        'config': self.get_macd_config(symbol),
                                        'workflow': name
                                    })
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Error parsing workflow {name}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error getting active symbols: {e}")
        
        self._set_to_cache(cache_key, symbols, ttl=self.cache_ttl)
        return symbols

    def invalidate_symbol_cache(self, symbol: str):
        """
        Invalidate cache for a specific symbol.
        """
        cache_key = self._generate_cache_key("macd_config", symbol=symbol)
        self._invalidate_cache(cache_key)
        # Also invalidate all symbols cache
        all_symbols_key = self._generate_cache_key("all_active_symbols")
        self._invalidate_cache(all_symbols_key)
