import time
import random
import requests

TRANSIENT_STATUS = {429, 500, 502, 503, 504}

def with_retries(fn, *, attempts: int = 5, base_delay: float = 0.8, jitter: float = 0.2):
    """
    Generic retry wrapper for transient HTTP failures.
    Exponential backoff: base_delay * 2^i with jitter.
    """
    last_err = None
    for i in range(max(1, attempts)):
        try:
            return fn()
        except requests.HTTPError as e:
            last_err = e
            status = getattr(e.response, "status_code", None)
            if status not in TRANSIENT_STATUS:
                raise
        except Exception as e:
            last_err = e
        
        # backoff
        sleep = base_delay * (2 ** i) + random.uniform(0, jitter)
        time.sleep(min(sleep, 10.0))
    
    # exhausted retries
    if last_err:
        raise last_err
    raise RuntimeError("retry_failed_unknown")
