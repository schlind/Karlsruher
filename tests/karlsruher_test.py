# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher
"""
Test Karlsruher
"""

from karlsruher.common import LockException
from karlsruher.housekeeping import HouseKeeper
from karlsruher.karlsruher import Karlsruher
from karlsruher.robot import Config

from .robot_test import RobotTestCase


class KarlsruherTest(RobotTestCase):

    def setUp(self):
        super().setUp()
        # Perform housekeeping for test data:
        HouseKeeper(
            config=Config(home=self.test_home),
            brain=self.test_brain,
            twitter=self.mock_twitter
        ).perform()
        # The bot to test:
        self.bot = Karlsruher(
            config=Config(home=self.test_home),
            brain=self.test_brain,
            twitter=self.mock_twitter
        )

    def test_can_have_advisors(self):
        """Karlsruher must have advisors."""
        self.bot.perform()
        self.assertEqual(1, self.bot.twitter.list_members.call_count)
        self.assertEqual(2, len(self.bot.advisors))
        self.assertTrue(str(self.mock_advisor_1.id) in self.bot.advisors)
        self.assertTrue(str(self.mock_advisor_2.id) in self.bot.advisors)
        self.assertFalse(str(self.mock_anyuser.id) in self.bot.advisors)

    def test_read_mentions_handles_lock(self):
        """Karlsruher must not ignore a lock."""
        self.bot.lock.acquire()
        self.assertRaises(LockException, self.bot.perform)
        self.assertTrue(self.bot.lock.is_acquired())

    def test_read_mention(self):
        """Karlsruher must read a mention."""
        self.assertTrue(self.bot.read_mention(self.mock_mention_from_nonfollower))

    def test_read_mention_only_once(self):
        """Karlsruher must not read a mention twice."""
        self.assertTrue(self.bot.read_mention(self.mock_mention_from_nonfollower))
        self.assertFalse(self.bot.read_mention(self.mock_mention_from_nonfollower))

    def test_ignore_myself(self):
        """Karlsruher must ignore itself."""
        self.assertFalse(self.bot.read_mention(self.mock_mention_by_myself))

    def test_read_mentions_timeline(self):
        """Karlsruher must read a mentions timeline."""
        self.bot.perform()
        self.assertEqual(9, self.bot.brain.count_tweets())
        self.assertEqual(9, self.bot.brain.count_tweets(Karlsruher.tweet_type))
        self.assertEqual(6, self.bot.brain.count_tweets(Karlsruher.tweet_type, comment='read_mention'))
        self.assertEqual(2, self.bot.brain.count_tweets(comment='advice_action'))
        self.assertEqual(1, self.bot.brain.count_tweets(comment='retweet_action'))

    # Feature "advice":

    def test_advice_can_accept_sleep(self):
        """Karlsruher must take advice sleep."""
        self.bot.perform()
        self.assertTrue(self.bot.advice_action(self.mock_mention_advice_gosleep))
        self.assertTrue(self.bot.brain.get(Karlsruher.sleeping))

    def test_advice_can_accept_wakeup(self):
        """Karlsruher must take advice wake up."""
        self.bot.perform()
        self.bot.brain.set(Karlsruher.sleeping, True)
        self.assertTrue(self.bot.advice_action(self.mock_mention_advice_wakeup))
        self.assertIsNone(self.bot.brain.get(Karlsruher.sleeping))

    def test_advice_can_ignore_from_non_advisors(self):
        """Karlsruher must ignore advice from non-advisor."""
        self.bot.perform()
        self.mock_mention_from_nonfollower.text = self.mock_mention_advice_gosleep.text
        self.assertFalse(self.bot.advice_action(self.mock_mention_from_nonfollower))

    def test_advice_ignore_unknown(self):
        """Karlsruher must ignore unkown advice."""
        self.bot.perform()
        self.assertFalse(self.bot.advice_action(self.mock_mention_advice_unknown))

    # Feature "retweet":

    def test_retweet_follower(self):
        """Karlsruher must retweet follower."""
        self.assertTrue(self.bot.retweet_action(self.mock_mention_by_follower_1))

    def test_retweet_not_during_sleep(self):
        """Karlsruher must not retweet during sleep."""
        self.bot.brain.set(Karlsruher.sleeping, True)
        self.assertFalse(self.bot.retweet_action(self.mock_mention_by_follower_1))

    def test_retweet_not_protected(self):
        """Karlsruher must not retweet protected followers."""
        self.assertFalse(self.bot.retweet_action(self.mock_mention_by_protected_follower))

    def test_retweet_not_replies(self):
        """Karlsruher must not retweet replies."""
        self.assertFalse(self.bot.retweet_action(self.mock_mention_reply_by_follower))

    def test_retweet_not_non_followers(self):
        """Karlsruher must not retweet non-followers."""
        self.assertFalse(self.bot.retweet_action(self.mock_mention_from_nonfollower))
