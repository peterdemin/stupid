from stupid.quotes import QuotesDatabase, BashOrgScrapper, Quote


def test_quote_random_smoke():
    # setup
    db = QuotesDatabase(':memory:')
    quotes = (
        Quote(1, 'a', False),
        Quote(2, 'b', False),
    )
    for quote in quotes:
        db.add(quote)
    # act
    random_quote = db.get_random()
    # assert
    assert random_quote in quotes


def test_scrapper():
    quotes = list(BashOrgScrapper().scrap("""
<html>
<body bgcolor="#ffffff" text="#000000" link="#c08000" vlink="#c08000" alink="#c08000">
<center>
    <table cellpadding="2" cellspacing="0" width="80%" border="0">
        <tr><td>Heading</td></tr>
    </table>
</center>

<center>
<table cellpadding="2" cellspacing="0" width="80%">
<tr><td valign='top'>
    <p class="quote"><a href="?244321" title="Permanent link to this quote."><b>#244321</b></a>
    <a href="./?le=e37ce763157364a1c99d09202feb5a67&amp;rox=244321" class="qa">+</a>
    (<font color="green">37357</font>)
    <a href="./?le=e37ce763157364a1c99d09202feb5a67&amp;sox=244321" class="qa">-</a>
    <a href="./?le=e37ce763157364a1c99d09202feb5a67&amp;sux=244321">[X]</a>
    </p>
    <p class="qt">
        First line<br />
        Second line<br />
    </p>
</td></tr></table>
</body>
</html>
    """))
    assert quotes == [Quote(244321, 'First line\nSecond line', False)]
