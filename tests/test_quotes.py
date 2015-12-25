from stupid.quotes import QuotesDatabase


def test_quote_random_smoke():
    QuotesDatabase().get_random()
