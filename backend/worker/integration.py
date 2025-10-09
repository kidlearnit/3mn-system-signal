"""
Lightweight integration helpers to bridge existing jobs with the new
DI container + Observer system (Phase 3 wiring).
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

from worker.container.service_container import ServiceContainer, ServiceConfig
from worker.strategies.base_strategy import Signal


def _make_container() -> ServiceContainer:
    """Create a ServiceContainer with sane defaults based on env vars."""
    cfg = ServiceConfig(
        enable_telegram=bool(os.getenv("TG_TOKEN")),
        enable_database=False,   # DB insert already done in legacy flow
        enable_websocket=True,
    )
    container = ServiceContainer(cfg)
    container.initialize_default_services()
    return container


def notify_signal(
    symbol: str,
    timeframe: str,
    signal_type: str,
    confidence: float,
    strength: float,
    strategy_name: str,
    details: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send a signal notification through the Observer system without
    changing legacy save paths. Returns True if at least one observer
    handled it successfully.
    """
    try:
        container = _make_container()
        notifier = container.get("signal_notifier")

        s = Signal(
            symbol=symbol,
            signal_type=signal_type,
            confidence=max(0.0, min(1.0, float(confidence))),
            strength=max(0.0, float(strength)),
            timeframe=timeframe,
            timestamp=datetime.now(),
            strategy_name=strategy_name,
            details=details or {},
        )

        results = notifier.notify_signal(s, event_type="new_signal")
        return any(results.values()) if isinstance(results, dict) else False
    except Exception:
        return False


