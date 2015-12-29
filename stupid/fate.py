import hashlib
import random
import re
import logging

from stupid.chatbot import ChatBot, trigger

logger = logging.getLogger('stupid.fate')

FINISH_PTRN = """
{0}
You can check target number by executing following code:
python -c 'import hashlib; print(hashlib.md5("{0}".encode("utf-8")).hexdigest()[:6])'
""".strip()

RULES_PTRN = """
Everyone picks a number between 1 and 100.
Then target number is posted.
The one, who picked number closest to target wins
Verification hash for this game is {hash}
""".strip()

VERIFIER_PTRN = 'Fate game #{game_id} target number: {number}'


class FateGameBot(ChatBot):
    """
    Helper class, that adapts FateGame to Slack chat
    """

    def __init__(self):
        self.game = None
        self.invitation_time = None

    @trigger
    def on_done(self):
        if self.game is not None:
            winner_info = self.game.determine_winner(self.game_messages())
            result = self.compose_result(winner_info)
            self.game = None
            return result

    @trigger
    def on_fate(self):
        self.game = FateGame()
        return self.game.invitation

    def compose_result(self, winner_info):
        result = self.verifier
        winner_info['username'] = self.username(winner_info['userid'])
        announcement = self.winner_announcement(winner_info)
        if announcement:
            result = '\n'.join([announcement, result])
        return self.good_bye.format(result)

    def winner_announcement(self, winner_info):
        return 'The winner is {username} with his bet {bet}'.format(winner_info)

    def on_posted(self, message):
        if self.game is not None:
            self.invitation_time = message['ts']

    @property
    def invitation(self):
        verifier_hash = self.easy_hash(self.game.verifier)
        return ("Everyone picks a number between 1 and 100.\n"
                "Then target number is posted.\n"
                "The one, who picked number closest to target wins\n"
                "Verification hash for this game is {0}".format(verifier_hash))

    def easy_hash(self, text):
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:6]


class FateGame(object):
    """
    Fair lottery for chats

    FateGame generates random number and posts it's hash.
    Users try to guess it, by posting messages.
    FateGame posts generated number and determines the winner.

    """
    good_bye = ("{0}\nYou can check target number by executing following code:\n"
                "python -c 'import hashlib; print(hashlib.md5(\"{0}\".encode(\"utf-8\")).hexdigest()[:6])'")
    re_numbers = re.compile(r'\b\d+\b')

    def __init__(self):
        self.setup_game()

    def determine_winner(self, messages):
        bets = self.parse_bets(messages)
        if bets:
            user_id, user_bet = self.winner_bet(bets)
            return {
                'user': user_id,
                'bet': user_bet,
            }

    def winner_bet(self, bets):
        return sorted(bets.items(), key=lambda a: abs(a[1] - self.target_nbr))[0]

    def parse_bets(self, messages):
        bets = {}
        for message in messages:
            current_bets = list(filter(self.is_valid_bet, self.parse_numbers(message['text'])))
            if current_bets and message['user'] not in bets:
                bets[message['user']] = current_bets[-1]
        return bets

    @staticmethod
    def parse_numbers(text):
        numbers = []
        for word in text.split():
            try:
                numbers.append(int(word))
            except ValueError:
                pass
        return numbers

    @staticmethod
    def is_valid_bet(number):
        return 0 < number < 100

    def setup_game(self):
        self.game_id = random.randint(1, 9999)
        self.target_nbr = random.randint(1, 100)
        self.verifier = VERIFIER_PTRN.format(game_id=self.game_id, number=self.target_nbr)
