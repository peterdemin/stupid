import functools
import datetime


def weekday(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if datetime.datetime.now().weekday() in range(0, 5):
            return func(*args, **kwargs)
    return wrapper
