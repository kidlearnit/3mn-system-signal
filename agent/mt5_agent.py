import os
import json
import time
import threading
from dataclasses import dataclass
from typing import Optional, Dict, Any


def _load_env():
    try:
        from dotenv import load_dotenv
        # Load project root .env if running from repo
        repo_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
        if os.path.exists(repo_env):
            load_dotenv(repo_env)
        else:
            load_dotenv()
    except Exception:
        pass


_load_env()


@dataclass
class AgentConfig:
    redis_url: str
    symbol: str
    broker_symbol: str
    symbol_prefix: str
    deviation: int
    default_volume: float
    tp_pct: float
    sl_pct: float
    magic: int
    login: Optional[int]
    password: Optional[str]
    server: Optional[str]
    terminal_path: Optional[str]


def load_config() -> AgentConfig:
    symbol = os.getenv('AGENT_SYMBOL', 'XAUUSD').strip()
    symbol_prefix = os.getenv('MT5_SYMBOL_PREFIX', '').strip()

    # Optional explicit map via env JSON, e.g. {"XAUUSD":"XAUUSD.a"}
    symbol_map_env = os.getenv('SYMBOL_MAP_JSON', '').strip()
    symbol_map: Dict[str, str] = {}
    if symbol_map_env:
        try:
            symbol_map = json.loads(symbol_map_env)
        except Exception:
            symbol_map = {}

    broker_symbol = symbol_map.get(symbol, f"{symbol_prefix}{symbol}")

    login_env = os.getenv('MT5_LOGIN')
    login_val = int(login_env) if login_env and login_env.isdigit() else None

    return AgentConfig(
        redis_url=os.getenv('AGENT_REDIS_URL', 'redis://localhost:6379/0'),
        symbol=symbol,
        broker_symbol=broker_symbol,
        symbol_prefix=symbol_prefix,
        deviation=int(os.getenv('MT5_DEVIATION', '20') or 20),
        default_volume=float(os.getenv('MT5_DEFAULT_VOLUME', '0.1') or 0.1),
        tp_pct=float(os.getenv('MT5_TP_PCT', '0') or 0),
        sl_pct=float(os.getenv('MT5_SL_PCT', '0') or 0),
        magic=int(os.getenv('MT5_MAGIC', '33001') or 33001),
        login=login_val,
        password=os.getenv('MT5_PASSWORD'),
        server=os.getenv('MT5_SERVER'),
        terminal_path=os.getenv('MT5_PATH'),
    )


def init_mt5(cfg: AgentConfig) -> bool:
    try:
        import MetaTrader5 as mt5
    except Exception as e:
        print(f"[MT5_AGENT] Failed to import MetaTrader5: {e}")
        return False

    try:
        if cfg.terminal_path:
            mt5.initialize(cfg.terminal_path)
        else:
            mt5.initialize()
    except Exception as e:
        print(f"[MT5_AGENT] mt5.initialize error: {e}")
        return False

    if not mt5.initialize():
        print(f"[MT5_AGENT] mt5.initialize failed: {mt5.last_error()}")
        return False

    if not (cfg.login and cfg.password and cfg.server):
        print("[MT5_AGENT] Missing MT5_LOGIN / MT5_PASSWORD / MT5_SERVER envs")
        return False

    ok = mt5.login(login=cfg.login, password=cfg.password, server=cfg.server)
    if not ok:
        print(f"[MT5_AGENT] mt5.login failed: {mt5.last_error()}")
        return False

    info = mt5.account_info()
    print(f"[MT5_AGENT] Logged in: {info.login if info else 'UNKNOWN'}")
    return True


class CandleAggregator:
    def __init__(self, symbol: str, tf_seconds: int = 60):
        self.symbol = symbol
        self.tf = tf_seconds
        self.current_bucket: Optional[int] = None
        self.ohlcv: Optional[Dict[str, Any]] = None

    def add_tick(self, ts_ms: int, price_bid: float, price_ask: float, volume: float):
        mid = (price_bid + price_ask) / 2.0
        bucket = (ts_ms // 1000) - ((ts_ms // 1000) % self.tf)
        if self.current_bucket is None or bucket > self.current_bucket:
            # New candle
            self.current_bucket = bucket
            self.ohlcv = {
                'ts': bucket,
                'open': mid,
                'high': mid,
                'low': mid,
                'close': mid,
                'volume': float(volume),
                'tf': '1m' if self.tf == 60 else f"{self.tf}s",
                'symbol': self.symbol,
            }
        else:
            # Update candle
            if mid > self.ohlcv['high']:
                self.ohlcv['high'] = mid
            if mid < self.ohlcv['low']:
                self.ohlcv['low'] = mid
            self.ohlcv['close'] = mid
            self.ohlcv['volume'] = float(self.ohlcv.get('volume', 0.0)) + float(volume)

    def get_current(self) -> Optional[Dict[str, Any]]:
        return self.ohlcv


def start_tick_stream(cfg: AgentConfig, stop_event: threading.Event):
    import redis
    import MetaTrader5 as mt5

    r = redis.from_url(cfg.redis_url)
    channel_ticks = f"mt5:ticks:{cfg.symbol}"
    channel_candles = f"mt5:candles:{cfg.symbol}:1m"

    # Ensure symbol is visible
    info = mt5.symbol_info(cfg.broker_symbol)
    if info is None:
        mt5.symbol_select(cfg.broker_symbol, True)

    aggregator = CandleAggregator(cfg.symbol, tf_seconds=60)
    print(f"[MT5_AGENT] Streaming ticks for {cfg.symbol} ({cfg.broker_symbol}) -> {channel_ticks}")

    last_pub_ts = 0
    while not stop_event.is_set():
        try:
            tick = mt5.symbol_info_tick(cfg.broker_symbol)
            if tick is None:
                time.sleep(0.2)
                continue

            ts_ms = int(time.time() * 1000)
            payload = {
                'symbol': cfg.symbol,
                'broker_symbol': cfg.broker_symbol,
                'ts': ts_ms,
                'bid': float(tick.bid),
                'ask': float(tick.ask),
                'last': float(getattr(tick, 'last', (tick.bid + tick.ask) / 2.0)),
                'volume': float(getattr(tick, 'volume', 0.0)),
            }
            r.publish(channel_ticks, json.dumps(payload))

            aggregator.add_tick(ts_ms, payload['bid'], payload['ask'], payload['volume'])
            cur_candle = aggregator.get_current()
            # Publish candle at most once per second
            now_s = int(time.time())
            if cur_candle and now_s != last_pub_ts:
                last_pub_ts = now_s
                r.publish(channel_candles, json.dumps(cur_candle))

            time.sleep(0.2)
        except Exception as e:
            print(f"[MT5_AGENT] Tick stream error: {e}")
            time.sleep(1)


def place_order(cfg: AgentConfig, order: Dict[str, Any]) -> Dict[str, Any]:
    import MetaTrader5 as mt5
    action = (order.get('action') or '').lower()
    volume = float(order.get('volume') or cfg.default_volume)
    sl = order.get('sl')
    tp = order.get('tp')
    symbol = order.get('symbol') or cfg.symbol
    if symbol != cfg.symbol:
        # Only trade configured symbol in this skeleton
        return {'ok': False, 'error': f'Unsupported symbol {symbol}', 'request': order}

    # Compute SL/TP by pct if not provided
    try:
        tick = mt5.symbol_info_tick(cfg.broker_symbol)
        if tick is None:
            return {'ok': False, 'error': 'No tick available', 'request': order}
        price_ref = tick.ask if action == 'buy' else tick.bid
        if sl is None and cfg.sl_pct > 0:
            sl = price_ref * (1 - cfg.sl_pct/100.0) if action == 'buy' else price_ref * (1 + cfg.sl_pct/100.0)
        if tp is None and cfg.tp_pct > 0:
            tp = price_ref * (1 + cfg.tp_pct/100.0) if action == 'buy' else price_ref * (1 - cfg.tp_pct/100.0)
    except Exception:
        pass

    symbol_info = mt5.symbol_info(cfg.broker_symbol)
    if symbol_info is None:
        mt5.symbol_select(cfg.broker_symbol, True)

    price = mt5.symbol_info_tick(cfg.broker_symbol).ask if action == 'buy' else mt5.symbol_info_tick(cfg.broker_symbol).bid
    order_type = mt5.ORDER_TYPE_BUY if action == 'buy' else mt5.ORDER_TYPE_SELL

    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': cfg.broker_symbol,
        'volume': float(volume),
        'type': order_type,
        'price': price,
        'sl': float(sl or 0.0),
        'tp': float(tp or 0.0),
        'deviation': cfg.deviation,
        'magic': cfg.magic,
        'comment': order.get('comment', 'auto-by-mt5-agent'),
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': mt5.ORDER_FILLING_FOK,
    }

    result = mt5.order_send(request)
    if result is None:
        return {'ok': False, 'error': 'order_send returned None', 'request': request}
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return {'ok': False, 'error': f"retcode {result.retcode}", 'result': getattr(result, '_asdict', lambda: {} )()}
    return {'ok': True, 'result': getattr(result, '_asdict', lambda: {} )()}


def start_order_listener(cfg: AgentConfig, stop_event: threading.Event):
    import redis
    r = redis.from_url(cfg.redis_url)
    pubsub = r.pubsub()
    orders_channel = 'mt5:orders'
    result_channel = 'mt5:orders:result'
    pubsub.subscribe(orders_channel)
    print(f"[MT5_AGENT] Listening orders on {orders_channel}")

    processed_keys = set()
    while not stop_event.is_set():
        try:
            msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if not msg:
                continue
            data = msg.get('data')
            if not data:
                continue
            try:
                order = json.loads(data)
            except Exception:
                continue

            key = order.get('idempotency_key') or json.dumps(order, sort_keys=True)
            if key in processed_keys:
                continue
            processed_keys.add(key)

            if (order.get('symbol') or cfg.symbol) != cfg.symbol:
                continue

            result = place_order(cfg, order)
            result['request_ref'] = key
            r.publish(result_channel, json.dumps(result))
        except Exception as e:
            print(f"[MT5_AGENT] Order listener error: {e}")
            time.sleep(1)


def main():
    cfg = load_config()
    print(f"[MT5_AGENT] Config: symbol={cfg.symbol}, broker_symbol={cfg.broker_symbol}, redis={cfg.redis_url}")
    if not init_mt5(cfg):
        print("[MT5_AGENT] Init failed. Exiting.")
        return

    stop_event = threading.Event()
    t_ticks = threading.Thread(target=start_tick_stream, args=(cfg, stop_event), daemon=True)
    t_orders = threading.Thread(target=start_order_listener, args=(cfg, stop_event), daemon=True)
    t_ticks.start()
    t_orders.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[MT5_AGENT] Stopping...")
        stop_event.set()
        t_ticks.join(timeout=2)
        t_orders.join(timeout=2)


if __name__ == '__main__':
    main()


