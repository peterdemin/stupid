from stupid.chatbot import ChatBot, trigger


class Dummy(ChatBot):
    @trigger
    def on_hello(self):
        return 'hello'

    @trigger
    def on_bye(self):
        return self.say_bye()

    def say_bye(self):
        return 'bye'


def test_trigger_magic():
    chatbot = Dummy()
    assert 'hello' == chatbot.on_message({'text': 'hello'})
    assert chatbot.triggers == {
        'hello': Dummy.on_hello,
        'bye': Dummy.on_bye,
    }
