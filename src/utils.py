from datetime import datetime, timezone, timedelta
from typing import Optional

def get_end_of_previous_period(dt: datetime, interval: str) -> datetime:
    """
    Calculates the end of the previous period for a given datetime and interval.
    For example, for 'minutes', it returns the last second of the previous minute.
    """
    if interval == "days":
        # End of previous day is 23:59:59.999999 of the day before
        return (dt.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(microseconds=1))
    elif interval == "hours":
        # End of previous hour is 59:59.999999 of the previous hour
        return (dt.replace(minute=0, second=0, microsecond=0) - timedelta(microseconds=1))
    elif interval == "minutes":
        # End of previous minute is 59.999999 of the previous minute
        return (dt.replace(second=0, microsecond=0) - timedelta(microseconds=1))
    else:
        raise ValueError(f"Unsupported interval: {interval}")

def map_interval_to_unit(interval: str) -> str:
    """
    Maps an interval string (e.g., '1d', '1h', '1m') to its corresponding unit string (e.g., 'days', 'hours', 'minutes').
    """
    if interval == "1d":
        return "days"
    elif interval == "1h":
        return "hours"
    elif interval == "1m":
        return "minutes"
    else:
        raise ValueError(f"Unsupported interval format: {interval}")