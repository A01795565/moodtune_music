import random
import time
from typing import Callable


def backoff_retry(fn: Callable, max_tries: int = 3, base_delay: float = 0.5, jitter: float = 0.25):
    last_exc = None
    for i in range(max_tries):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if i == max_tries - 1:
                break
            time.sleep(base_delay * (2 ** i) + random.random() * jitter)
    raise last_exc

