import unittest

import pytest
from mock import patch, ANY

import stupid

stupid.logging.disable(stupid.logging.CRITICAL)


def test_jobs():
    stupid.schedule.every().day.at("11:55").do(print_some)
    stupid.schedule.every().day.at("15:55").do(print_some)
    stupid.schedule.every().day.at("17:15").do(print_some)
    stupid.schedule.every().day.at("9:30").do(print_some)
    stupid.render_jobs()
    stupid.schedule.default_scheduler.run_all()


def test_quote():
    quote = stupid.Quotes().get_random_quote()
    stupid.logger.debug(quote)


@patch('stupid.run_forever')
def test_main_runs_forever(run_forever):
    stupid.main()
    run_forever.assert_called_once_with()


@patch('stupid.read_new_messages')
class AskForReplyTestCase(unittest.TestCase):
    def test_ask_for_reply_timeout(self, read_new_messages):
        retval = stupid.ask_for_reply([], 0)
        assert retval == stupid.schedule.CancelJob

    def test_ask_for_reply_waits_for_first_human(self, read_new_messages):
        retval = stupid.ask_for_reply([], stupid.time.time())
        stupid.read_new_messages.assert_called_once_with(ANY)
        assert retval is None

    @patch('stupid.post')
    def test_ask_for_reply_one(self, post, read_new_messages):
        read_new_messages.return_value = [{'user': 1}]
        ts = stupid.time.time()
        retval = stupid.ask_for_reply({1: 'a', 2: 'b'}, ts)
        assert retval == stupid.schedule.CancelJob
        read_new_messages.assert_called_once_with(ts)
        messages = [x[0][0] for x in post.call_args_list]
        assert len(messages) == 1
        assert '@b,' in messages[0]


def test_fate():
    fate = stupid.FateGame.start()
    assert type(fate.invitation) == str
    assert type(fate.verifier) == str


@patch('stupid.read_new_messages', return_value=[{'text': '@' + stupid.MY_ID + ' a', 'ts': 0}])
def test_reader(read_new_messages):
    handler = DummyHandler()
    reader = stupid.Reader(handler)
    reader.read()
    assert handler.called is True


class DummyHandler(object):
    triggers = 'a'

    def on_message(self, text):
        self.called = True
        return None


@stupid.weekday
def print_some():
    print('ok')


if __name__ == '__main__':
    pytest.main()
