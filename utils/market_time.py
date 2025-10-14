from datetime import datetime, time
from zoneinfo import ZoneInfo

def is_market_open(exchange: str) -> bool:
    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")) if exchange in {"HOSE","HNX","UPCOM","VN"} else datetime.now(ZoneInfo("America/New_York"))
    t = now.time()
    if exchange in {"HOSE","HNX","UPCOM","VN"}:
        return time(9,0) <= t <= time(11,30) or time(13,0) <= t <= time(15,0)
    # US typical session
    return time(9,30) <= t <= time(16,0)

