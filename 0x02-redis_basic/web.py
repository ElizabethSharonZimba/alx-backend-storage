#!/usr/bin/env python3

import redis
import requests
from functools import wraps
from typing import Callable

client = redis.Redis()

def track_get_page(fn: Callable) -> Callable:
    """Decorator for get_page to track URL requests and cache responses."""
    @wraps(fn)
    def wrapper(url: str) -> str:
        """Wrapper that checks cache and tracks URL requests."""
        client.incr(f'count:{url}')
        cached_page = client.get(url)
        if cached_page:
            return cached_page.decode('utf-8')
        response = fn(url)
        client.setex(url, 10, response)
        return response
    return wrapper

@track_get_page
def get_page(url: str) -> str:
    """Makes an HTTP request to a given URL."""
    response = requests.get(url)
    return response.text

