from __future__ import annotations

import time
from typing import Callable, Dict, Tuple
from fastapi import Request, HTTPException, status

# In-memory token buckets keyed by (namespace, ip)
_buckets: Dict[Tuple[str, str], Tuple[float, float, int]] = {}
# (last_refill_ts, refill_interval_s, tokens)


def rate_limit(namespace: str, capacity: int = 20, refill_interval_seconds: float = 1.0) -> Callable[[Request], None]:
    """Simple per-IP token bucket dependency for hot endpoints.

    namespace: logical bucket name per endpoint
    capacity: max requests allowed per bucket per interval window
    refill_interval_seconds: time window length for capacity reset
    """

    def _dep(request: Request) -> None:
        ip = (request.client.host if request and request.client else "unknown")
        key = (namespace, ip)
        now = time.monotonic()
        last, interval, tokens = _buckets.get(key, (now, refill_interval_seconds, capacity))
        if now - last >= interval:
            # Refill
            last = now
            tokens = capacity
        if tokens <= 0:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate_limited")
        tokens -= 1
        _buckets[key] = (last, refill_interval_seconds, tokens)

    return _dep
