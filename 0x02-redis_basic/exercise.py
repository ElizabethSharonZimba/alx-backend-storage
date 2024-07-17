#!/usr/bin/env python3
""" Redis client module
"""
import redis
from uuid import uuid4
from functools import wraps
from typing import Any, Callable, Optional, Union


def count_calls(method: Callable) -> Callable:
    """ Decorator for Cache class methods to track call count
    """
    @wraps(method)
    def wrapper(self: Any, *args, **kwargs) -> Any:
        """ Wraps called method and increments its call count in redis
        """
        self._redis.incr(method.__qualname__)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """ Decorator for Cache class method to track arguments and output
    """
    @wraps(method)
    def wrapper(self: Any, *args, **kwargs) -> Any:
        """ Wraps called method and tracks its passed arguments and output
        """
        self._redis.rpush(f'{method.__qualname__}:inputs', str(args))
        output = method(self, *args, **kwargs)
        self._redis.rpush(f'{method.__qualname__}:outputs', output)
        return output
    return wrapper


def replay(fn: Callable) -> None:
    """ Display the history of calls of a particular function
    """
    client = redis.Redis()
    calls = client.get(fn.__qualname__).decode('utf-8')
    inputs = [input.decode('utf-8') for input in
              client.lrange(f'{fn.__qualname__}:inputs', 0, -1)]
    outputs = [output.decode('utf-8') for output in
               client.lrange(f'{fn.__qualname__}:outputs', 0, -1)]
    print(f'{fn.__qualname__} was called {calls} times:')
    for input, output in zip(inputs, outputs):
        print(f'{fn.__qualname__}(*{input}) -> {output}')


class Cache:
    """ Caching class
    """
    def __init__(self) -> None:
        """ Initialize a new cache object
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """ Stores data in redis with a randomly generated key
        """
        key = str(uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable] = None) -> Any:
        """ Retrieve value from redis and convert it to the correct type
        """
        value = self._redis.get(key)
        if value is None:
            return None
        if fn:
            return fn(value)
        return value

    def get_str(self, data: bytes) -> str:
        """ Converts bytes to string
        """
        return data.decode('utf-8')

    def get_int(self, data: bytes) -> int:
        """ Converts bytes to integer
        """
        return int(data)

