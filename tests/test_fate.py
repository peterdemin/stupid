import pytest

from stupid.fate import FateGame


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


if __name__ == '__main__':
    pytest.main()
