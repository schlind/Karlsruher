# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher

"""
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
        """The bot should have advisors."""
        self.bot.perform()
        self.assertEqual(1, self.bot.twitter.list_members.call_count)
        self.assertEqual(2, len(self.bot.advisors))
        self.assertTrue(str(self.mock_advisor_1.id) in self.bot.advisors)
        self.assertTrue(str(self.mock_advisor_2.id) in self.bot.advisors)
        self.assertFalse(str(self.mock_anyuser.id) in self.bot.advisors)

    def test_read_mentions_handles_lock(self):
        self.bot.lock.acquire()
        self.assertRaises(LockException, self.bot.perform)
        self.assertTrue(self.bot.lock.is_acquired())

    def test_read_mention(self):
        """The bot can read a mention."""
        self.assertTrue(self.bot.read_mention(self.mock_mention_from_nonfollower))

    def test_read_mention_only_once(self):
        """The bot does read a mention only once."""
        self.assertTrue(self.bot.read_mention(self.mock_mention_from_nonfollower))
        self.assertFalse(self.bot.read_mention(self.mock_mention_from_nonfollower))

    def test_ignore_myself(self):
        self.assertFalse(self.bot.read_mention(self.mock_mention_by_myself))


    def test_read_mentions_timeline(self):
        self.bot.perform()
        self.assertEqual(9, self.bot.brain.count_tweets())
        self.assertEqual(9, self.bot.brain.count_tweets(Karlsruher.tweet_type))
        self.assertEqual(6, self.bot.brain.count_tweets(Karlsruher.tweet_type, comment='read_mention'))
        self.assertEqual(2, self.bot.brain.count_tweets(comment='advice_action'))
        self.assertEqual(1, self.bot.brain.count_tweets(comment='retweet_action'))


    # Feature "advice":


    def test_advice_can_accept_sleep(self):
        self.bot.perform()
        self.assertTrue(self.bot.advice_action(self.mock_mention_advice_gosleep))
        self.assertTrue(self.bot.brain.get('retweet.disabled'))

    def test_advice_can_accept_wakeup(self):
        self.bot.perform()
        self.bot.brain.set('retweet.disabled', True)
        self.assertTrue(self.bot.advice_action(self.mock_mention_advice_wakeup))
        self.assertIsNone(self.bot.brain.get('retweet.disabled'))


    def test_advice_can_ignore_from_non_advisors(self):
        self.bot.perform()
        self.mock_mention_from_nonfollower.text = self.mock_mention_advice_gosleep.text
        self.assertFalse(self.bot.advice_action(self.mock_mention_from_nonfollower))

    def test_advice_ignore_unknown(self):
        self.bot.perform()
        self.assertFalse(self.bot.advice_action(self.mock_mention_advice_unknown))


    # Feature "retweet":

    def test_retweet_follower(self):
        self.assertTrue(self.bot.retweet_action(self.mock_mention_by_follower_1))

    def test_retweet_not_during_sleep(self):
        self.bot.brain.set('retweet.disabled', True)
        self.assertFalse(self.bot.retweet_action(self.mock_mention_by_follower_1))

    def test_retweet_not_protected(self):
        self.assertFalse(self.bot.retweet_action(self.mock_mention_by_protected_follower))

    def test_retweet_not_replies(self):
        self.assertFalse(self.bot.retweet_action(self.mock_mention_reply_by_follower))

    def test_retweet_not_non_followers(self):
        self.assertFalse(self.bot.retweet_action(self.mock_mention_from_nonfollower))
