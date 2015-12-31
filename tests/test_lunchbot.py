import time
import unittest
from stupid.lunchbot import LunchBot
from mock import patch, ANY, MagicMock


class AskForReplyTestCase(unittest.TestCase):
    def setUp(self):
        self.bot = LunchBot(broker=MagicMock())

    def test_ask_for_reply_timeout(self):
        self.bot.ask_for_reply_after = 0
        self.bot.on_timeout()
        assert self.bot.ask_for_reply_after is None

    def test_ask_for_reply_waits_for_first_human(self):
        self.bot.ask_for_reply_after = time.time()
        retval = self.bot.ask_for_reply()
        self.bot.broker.read_new_messages.assert_called_once_with(ANY)
        assert retval is False

    def test_ask_for_reply_one(self):
        self.bot.broker.read_new_messages.return_value = [{'user': 1}]
        self.bot.ask_for_reply_after = time.time()
        self.bot.users_to_ask = {1: 'a', 2: 'b'}
        retval = self.bot.ask_for_reply()
        assert retval is True
        self.bot.broker.read_new_messages.assert_called_once_with(ANY)
        messages = [x[0][0] for x in self.bot.broker.post.call_args_list]
        assert len(messages) == 1
        assert '@b,' in messages[0]
