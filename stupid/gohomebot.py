from stupid.chatbot import ChatBot
from stupid.utils import weekday


class GoHomeBot(ChatBot):
    def __init__(self, *args, **kwargs):
        super(GoHomeBot, self).__init__(*args, **kwargs)
        self.schedule.every().day.at("17:15").do(self.post_go_home)

    @weekday
    def post_go_home(self):
        return self.broker.post("Russian, go home", color='warning')
