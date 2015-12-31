import pytest

from stupid.fate import FateGame, FateGameBot
from stupid.slackbroker import SlackBroker
from mock import MagicMock


def test_fate():
    game = FateGame()
    winner_info = game.determine_winner([
        {'user': user, 'text': bet}
        for user, bet in zip('abc', '123')
    ])
    assert winner_info['user'] in 'abc'
    assert winner_info['bet'] in [1, 2, 3]


def test_parse_bets():
    bets = FateGame().parse_bets([
        {'user': 'a', 'text': '1'},
        {'user': 'b', 'text': '1 or 2'},
        {'user': 'c', 'text': '-100'},
        {'user': 'd', 'text': '3.141592589'},
    ])
    assert bets == {
        'a': 1,
        'b': 2,
    }


def test_chat_scenario():
    broker = MagicMock(spec=SlackBroker)
    broker.username.return_value = 'U'
    bot = FateGameBot(broker)
    rules = bot.on_message({"user": "x", "text": "@stupid: determine our fate"})
    assert bot.game is not None
    assert 'picks a number' in rules
    broker.post.assert_called_once_with(rules)
    broker.messages.return_value = [
        {"user": "a", "text": "25"},
        {"user": "b", "text": "50"},
        {"user": "c", "text": "75"},
    ]
    game_over = bot.on_message({"user": "x", "text": "@stupid: we're done"})
    assert 'The winner is' in game_over


if __name__ == '__main__':
    pytest.main()
