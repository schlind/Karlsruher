'''
KarlsruherTest
'''

from karlsruher.common import LockException
from karlsruher.karlsruher import Karlsruher
from .robot_test import RobotTestCase

class KarlsruherTest(RobotTestCase):
    '''Test the Karlsruher'''

    def setUp(self):
        '''Create Karlsruher instance, do housekeeping for testdata'''
        super().setUp()
        self.bot = Karlsruher(self.test_home, self.test_brain, self.mock_twitter)
        self.bot.housekeeping()

    def test_can_handle_lock(self):
        '''Must not perform during lock'''
        self.bot.lock.acquire()
        self.assertRaises(LockException, self.bot.feature_retweets)

    def test_can_perform(self):
        '''Must perform and retweet 2 mentions'''
        self.bot.act_delay = 0
        self.bot.feature_retweets()
        self.assertEqual(2, self.bot.twitter.retweet.call_count)

    def test_can_apply_retweet(self):
        '''Retweet mention by non-protected followers, when mention is not a reply'''
        self.bot.act_delay = 0
        self.assertFalse(self.bot.retweet_applies(self.tweet_by_myself))
        self.assertFalse(self.bot.retweet_applies(self.tweet_by_protected_follower))
        self.assertFalse(self.bot.retweet_applies(self.tweet_reply_by_follower))
        self.assertFalse(self.bot.retweet_applies(self.tweet_from_nonfollower))
        self.bot.act_on_twitter = False
        self.assertTrue(self.bot.retweet_applies(self.tweet_by_follower_1))
        self.assertEqual(0, self.bot.twitter.retweet.call_count)
        self.bot.act_on_twitter = True
        self.assertTrue(self.bot.retweet_applies(self.tweet_by_follower_2))
        self.assertEqual(1, self.bot.twitter.retweet.call_count)
