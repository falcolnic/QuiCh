import threading
from datetime import datetime, timedelta
from typing import Dict, Tuple


class RateLimitExceededException(Exception):
    def __init__(
        self,
        message: str = "Rate limit exceeded. Please register to continue searching.",
    ):
        self.message = message
        super().__init__(self.message)


_rate_limit_cache: Dict[str, Tuple[int, datetime]] = {}
_cache_lock = threading.Lock()


def check_rate_limit(ip_address: str, is_authenticated: bool = False) -> bool:
    if is_authenticated:
        return True

    MAX_REQUESTS = 5
    RESET_PERIOD_HOURS = 24
    current_time = datetime.utcnow()

    with _cache_lock:
        if ip_address not in _rate_limit_cache:
            _rate_limit_cache[ip_address] = (1, current_time)
            return True

        count, last_reset = _rate_limit_cache[ip_address]

        if current_time - last_reset > timedelta(hours=RESET_PERIOD_HOURS):
            _rate_limit_cache[ip_address] = (1, current_time)
            return True

        if count >= MAX_REQUESTS:
            remaining_time = (
                last_reset + timedelta(hours=RESET_PERIOD_HOURS)
            ) - current_time
            hours_remaining = int(remaining_time.total_seconds() / 3600)
            minutes_remaining = int((remaining_time.total_seconds() % 3600) / 60)

            raise RateLimitExceededException(
                f"You've exceeded the limit of {MAX_REQUESTS} searches. "
                f"Please register for unlimited searches or try again in {hours_remaining}h {minutes_remaining}m."
            )

        _rate_limit_cache[ip_address] = (count + 1, last_reset)
        return True


def get_remaining_requests(ip_address: str, is_authenticated: bool = False) -> dict:
    if is_authenticated:
        return {"unlimited": True, "remaining": "∞"}

    MAX_REQUESTS = 5
    current_time = datetime.utcnow()

    with _cache_lock:
        if ip_address not in _rate_limit_cache:
            return {"unlimited": False, "remaining": MAX_REQUESTS, "used": 0}

        count, last_reset = _rate_limit_cache[ip_address]

        if current_time - last_reset > timedelta(hours=24):
            return {"unlimited": False, "remaining": MAX_REQUESTS, "used": 0}

        remaining = max(0, MAX_REQUESTS - count)
        return {
            "unlimited": False,
            "remaining": remaining,
            "used": count,
            "max": MAX_REQUESTS,
        }


def cleanup_expired_entries():
    current_time = datetime.utcnow()
    expired_ips = []

    with _cache_lock:
        for ip, (count, last_reset) in _rate_limit_cache.items():
            if current_time - last_reset > timedelta(hours=25):
                expired_ips.append(ip)

        for ip in expired_ips:
            del _rate_limit_cache[ip]
