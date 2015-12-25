import pytest

from stupid.fate import FateGame


def test_fate():
    game = FateGame.start()
    assert type(game.invitation) == str
    assert type(game.verifier) == str


if __name__ == '__main__':
    pytest.main()
