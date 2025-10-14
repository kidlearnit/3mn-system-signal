from typing import Any, Optional

def fmt_val(value: Optional[float], fmt: str = ".2f") -> str:
    if value is None:
        return "-"
    try:
        return format(float(value), fmt)
    except Exception:
        return str(value)


