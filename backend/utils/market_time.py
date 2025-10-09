import pytz
import os
from datetime import datetime, date, time as dtime

# Configurable timezones based on environment
DEFAULT_TIMEZONE = os.getenv('TIMEZONE', 'Asia/Ho_Chi_Minh')
DEPLOYMENT_TZ = pytz.timezone(DEFAULT_TIMEZONE)

# Market-specific timezones (always correct regardless of deployment location)
VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")
US_TZ = pytz.timezone("US/Eastern")

# Ngày nghỉ cố định VN (MM, DD)
VN_HOLIDAYS = [
    (1, 1),   # Tết Dương lịch
    (4, 30),  # Giải phóng miền Nam
    (5, 1),   # Quốc tế Lao động
    (9, 2),   # Quốc khánh
]

# Ngày nghỉ cố định US (MM, DD)
US_HOLIDAYS = [
    (1, 1),   # New Year’s Day
    (7, 4),   # Independence Day
    (12, 25), # Christmas Day
]

from datetime import date, timedelta
from lunardate import LunarDate

def tet_holidays(year:int, days_before:int=2, days_after:int=3):
    """
    Trả về danh sách ngày nghỉ Tết Nguyên Đán (dương lịch) cho 1 năm.
    - year: năm dương lịch chứa mùng 1 Tết âm
    - days_before: số ngày nghỉ trước mùng 1
    - days_after: số ngày nghỉ sau mùng 1
    """
    # Mùng 1 tháng Giêng âm lịch của năm
    tet_start = LunarDate(year, 1, 1).toSolarDate()

    # Thêm các ngày trước và sau
    holidays = []
    for offset in range(-days_before, days_after+1):
        holidays.append(tet_start + timedelta(days=offset))
    return holidays


def is_us_floating_holiday(dt: date) -> bool:
    """Kiểm tra các ngày nghỉ lễ Mỹ không cố định"""
    # Martin Luther King Jr. Day: Thứ 2 tuần thứ 3 tháng 1
    if dt.month == 1 and dt.weekday() == 0 and 15 <= dt.day <= 21:
        return True
    # Presidents’ Day: Thứ 2 tuần thứ 3 tháng 2
    if dt.month == 2 and dt.weekday() == 0 and 15 <= dt.day <= 21:
        return True
    # Memorial Day: Thứ 2 cuối tháng 5
    if dt.month == 5 and dt.weekday() == 0 and dt.day + 7 > 31:
        return True
    # Labor Day: Thứ 2 đầu tháng 9
    if dt.month == 9 and dt.weekday() == 0 and dt.day <= 7:
        return True
    # Thanksgiving Day: Thứ 5 tuần thứ 4 tháng 11
    if dt.month == 11 and dt.weekday() == 3 and 22 <= dt.day <= 28:
        return True
    # Good Friday: Thứ 6 trước Chủ Nhật Phục Sinh (tính toán phức tạp, có thể bổ sung sau)
    return False

def is_market_open(exchange: str):
    """
    Trả về tuple: (is_open, time_to_close, time_to_open)
    - is_open: True/False
    - time_to_close: timedelta hoặc None
    - time_to_open: timedelta hoặc None
    """
    now_vn = datetime.now(VN_TZ)
    now_us = datetime.now(US_TZ)

    # --- VN ---
    if exchange in ("HOSE", "HNX", "UPCOM"):
        weekday = now_vn.weekday()
        if weekday >= 5:  # Thứ 7, CN
            # Tính tới 9:00 sáng thứ 2
            days_ahead = (7 - weekday) % 7
            next_open = VN_TZ.localize(datetime.combine(
                (now_vn + timedelta(days=days_ahead)).date(),
                dtime(9, 0)
            ))
            return False, None, next_open - now_vn

        morning_start = VN_TZ.localize(datetime.combine(now_vn.date(), dtime(9, 0)))
        morning_end   = VN_TZ.localize(datetime.combine(now_vn.date(), dtime(11, 30)))
        afternoon_start = VN_TZ.localize(datetime.combine(now_vn.date(), dtime(13, 0)))
        afternoon_end   = VN_TZ.localize(datetime.combine(now_vn.date(), dtime(15, 0)))

        if morning_start <= now_vn <= morning_end:
            return True, morning_end - now_vn, None
        elif afternoon_start <= now_vn <= afternoon_end:
            return True, afternoon_end - now_vn, None
        elif now_vn < morning_start:
            return False, None, morning_start - now_vn
        elif morning_end < now_vn < afternoon_start:
            return False, None, afternoon_start - now_vn
        else:
            # Sau 15:00 → tới 9:00 sáng hôm sau
            next_open = morning_start + timedelta(days=1)
            return False, None, next_open - now_vn

    # --- US ---
    elif exchange in ("NASDAQ", "NYSE"):
        weekday = now_us.weekday()
        if weekday >= 5:  # Thứ 7, CN
            # Tính tới 9:30 sáng thứ 2
            days_ahead = (7 - weekday) % 7
            next_open = US_TZ.localize(datetime.combine(
                (now_us + timedelta(days=days_ahead)).date(),
                dtime(9, 30)
            ))
            return False, None, next_open - now_us

        market_start = US_TZ.localize(datetime.combine(now_us.date(), dtime(9, 30)))
        market_end   = US_TZ.localize(datetime.combine(now_us.date(), dtime(16, 0)))

        if market_start <= now_us <= market_end:
            return True, market_end - now_us, None
        elif now_us < market_start:
            return False, None, market_start - now_us
        else:
            # Sau 16:00 → tới 9:30 sáng hôm sau
            next_open = market_start + timedelta(days=1)
            return False, None, next_open - now_us

    else:
        raise ValueError(f"Unknown exchange: {exchange}")
