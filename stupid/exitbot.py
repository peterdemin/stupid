import sys
import logging

from stupid.chatbot import ChatBot, trigger


logger = logging.getLogger('stupid.exit')


class ExitBot(ChatBot):

    def __init__(self, *args, **kwargs):
        super(ExitBot, self).__init__(*args, **kwargs)

    @trigger
    def on_exit(self):
        if self.iteration_nbr == 0:
            return "Restarted successfuly"
        else:
            logger.info("Exiting on demand")
            sys.exit(0)

    @trigger
    def on_restart(self):
        return self.on_exit()
