import inspect


def trigger(method):
    method.is_trigger = True
    return method


class ChatBot(object):
    triggers = {}

    def on_message(self, message):
        if not self.triggers:
            self.introspect()
        text = message['text'].lower()
        for trigger in self.triggers:
            if trigger in text:
                return self.triggers[trigger](self)

    def username(self, userid):
        return 'Petr'

    def game_messages(self):
        return []

    @classmethod
    def introspect(cls):
        for name, method in inspect.getmembers(cls, predicate=inspect.ismethod):
            if name.startswith('on_'):
                if getattr(method, 'is_trigger', False) is True:
                    event_name = name[3:]
                    cls.triggers[event_name] = method

