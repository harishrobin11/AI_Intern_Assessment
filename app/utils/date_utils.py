from datetime import datetime, timezone
from typing import Optional
import pandas as pd

def parse_datetime(val: str) -> Optional[datetime]:
    if not val or pd.isna(val):
        return None
    try:
        return pd.to_datetime(val).to_pydatetime()
    except Exception:
        return None

def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    if dt is None or pd.isna(dt):
        return None
    if isinstance(dt, pd.Timestamp):
        return dt.strftime("%Y-%m-%d %H:%M")
    return dt.strftime("%Y-%m-%d %H:%M")
