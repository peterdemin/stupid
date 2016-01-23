from datetime import date
from stupid.holydaybot import HolydayBot
from mock import patch, Mock


def test_holiday_title_for_new_year():
    bot = HolydayBot()
    assert "New Year's Day" == bot.holyday_title(date(2016, 1, 1))


def test_holiday_title_for_day_after_new_year():
    bot = HolydayBot()
    assert bot.holyday_title(date(2016, 1, 2)) is None


@patch("stupid.holydaybot.datetime.date")
def test_next_week_holiday_announcement(mock_date):
    mock_date.today.return_value = date(2016, 1, 11)
    mock_broker = Mock()
    bot = HolydayBot(broker=mock_broker)
    bot.post_next_week_holyday()
    mock_broker.post.assert_called_once_with(
        "On the next week Monday, January 18 is day off - Martin Luther King Jr. Day.",
        color='info'
    )
