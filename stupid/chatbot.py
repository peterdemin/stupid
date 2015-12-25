import inspect
import logging


logger = logging.getLogger(__name__)


def trigger(method):
    method.is_trigger = True
    return method


def every_minute(method):
    method.every_minute = True
    return method


class ChatBot(object):
    triggers = {}
    pollers = []

    def __init__(self, broker=None):
        self.broker = broker
        if self.broker is not None:
            self.username = self.broker.username
            self.messages = self.broker.messages

    def on_message(self, message):
        if not self.triggers:
            self.introspect()
        text = message['text'].lower()
        for trigger in self.triggers:
            if trigger in text:
                return self.triggers[trigger](self)

    @classmethod
    def introspect(cls):
        for name, method in inspect.getmembers(cls, predicate=inspect.ismethod):
            if name.startswith('on_'):
                if getattr(method, 'is_trigger', False) is True:
                    event_name = name[3:]
                    cls.triggers[event_name] = method
                if getattr(method, 'every_minute', False) is True:
                    cls.pollers.append(method)
