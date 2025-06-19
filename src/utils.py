from datetime import datetime, timezone
from typing import Optional

def get_end_of_previous_period(dt: datetime, interval: str) -> datetime:
    """
    Calculates the end of the previous period for a given datetime and interval.
    This is equivalent to the start of the current period.
    """
    if interval == "days":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif interval == "hours":
        return dt.replace(minute=0, second=0, microsecond=0)
    elif interval == "minutes":
        return dt.replace(second=0, microsecond=0)
    else:
        raise ValueError(f"Unsupported interval: {interval}")