import hashlib
import random
import re
import logging
from collections import OrderedDict

from stupid.chatbot import ChatBot, trigger

logger = logging.getLogger('stupid.fate')

FINISH_PTRN = """
{announcement}
{verifier}
You can check target number by executing following code:
python -c 'import hashlib; print(hashlib.md5("{verifier}".encode("utf-8")).hexdigest()[:6])'
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

    def __init__(self, *args, **kwargs):
        super(FateGameBot, self).__init__(*args, **kwargs)
        self.game = None
        self.invitation_time = None

    @trigger
    def on_done(self):
        if self.game is not None:
            winner_info = self.game.determine_winner(self.game_messages())
            if winner_info:
                result = self.compose_result(winner_info)
                self.game = None
                return result

    @trigger
    def on_fate(self):
        self.game = FateGame()
        return self.invitation

    def game_messages(self):
        return self.broker.messages(self.invitation_time)

    def compose_result(self, winner_info):
        winner_info['username'] = self.username(winner_info['user'])
        announcement = self.winner_announcement(winner_info)
        return FINISH_PTRN.format(
            announcement=announcement,
            verifier=self.game.verifier,
        ).strip()

    def winner_announcement(self, winner_info):
        return 'The winner is :medal: {username} with his bet {bet}'.format(**winner_info)

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
    re_numbers = re.compile(r'\b\d+\b')

    def __init__(self):
        self.setup_game()

    def determine_winner(self, messages):
        bets = self.parse_bets(messages)
        if bets:
            user, user_bet = self.winner_bet(bets)
            return {
                'user': user,
                'bet': user_bet,
            }

    def winner_bet(self, bets):
        distances = sorted([(abs(bet - self.target_nbr), bet)
                            for bet in bets.values()])
        closest_bets = set([bet
                            for distance, bet in distances
                            if distance == distances[0][0]])
        for user, bet in bets.items():
            if bet in closest_bets:
                return user, bet

    def parse_bets(self, messages):
        bets = OrderedDict()
        for message in messages:
            if 'user' in message and 'text' in message:  # filter out bots
                user, text = message['user'], message['text']
                current_bets = list(filter(self.is_valid_bet, self.parse_numbers(text)))
                if current_bets and user not in bets:
                    if user in bets:
                        del bets[user]
                    bets[user] = current_bets[-1]
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
