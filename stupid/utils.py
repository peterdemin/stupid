import functools
import datetime
import logging


logger = logging.getLogger(__name__)


def weekday(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if datetime.date.today().weekday() in range(0, 5):
            return func(*args, **kwargs)
        else:
            logger.debug("Skipping {0} since it is not a weekday".format(func))

    return wrapper
