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


def test_equal_bets():
    game = FateGame()
    info1 = game.determine_winner([
        {'user': 'a', 'text': '50'},
        {'user': 'b', 'text': '50'},
        {'user': 'c', 'text': '50'},
        {'user': 'd', 'text': '50'},
    ])
    assert info1 == {'user': 'a', 'bet': 50}
    info2 = game.determine_winner([
        {'user': 'd', 'text': '50'},
        {'user': 'c', 'text': '50'},
        {'user': 'b', 'text': '50'},
        {'user': 'a', 'text': '50'},
    ])
    assert info2 == {'user': 'd', 'bet': 50}


def test_chat_scenario():
    broker = MagicMock(spec=SlackBroker)
    broker.username.return_value = 'U'
    bot = FateGameBot(broker)
    rules = bot.on_message(1, {"user": "x", "text": "@stupid: determine our fate"})
    assert bot.game is not None
    assert 'picks a number' in rules
    broker.post.assert_called_once_with(rules)
    broker.messages.return_value = [
        {"user": "a", "text": "25"},
        {"user": "b", "text": "50"},
        {"user": "c", "text": "75"},
    ]
    game_over = bot.on_message(2, {"user": "x", "text": "@stupid: we're done"})
    assert 'The winner is' in game_over


if __name__ == '__main__':
    pytest.main()
