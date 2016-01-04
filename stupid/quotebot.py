from stupid.chatbot import ChatBot
from stupid.quotes import QuotesDatabase
from stupid.utils import weekday


class QuoteBot(ChatBot):
    def __init__(self, *args, **kwargs):
        super(QuoteBot, self).__init__(*args, **kwargs)
        self.schedule.every().day.at("9:25").do(self.post_quote)
        self.registry = QuotesDatabase()

    @weekday
    def post_quote(self):
        quote = self.registry.get_random()
        self.broker.post(">>>" + quote.text)
        self.registry.mark_as_shown(quote)
