'''
KarlsruherTest
'''

from unittest import mock

from karlsruher.common import LockException
from karlsruher.karlsruher import Karlsruher
from karlsruher.twitter import TwitterException
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

    def test_error_handling_retweet(self):
        '''Exceptions must not stop process in loop'''
        self.bot.twitter.retweet = mock.Mock(side_effect=TwitterException('Expect me!'))
        self.bot.act_delay = 0
        self.bot.has_tweet = mock.Mock(return_value=False)
        self.bot.feature_retweets()
        self.bot.feature_retweets()
        self.bot.has_tweet = mock.Mock(return_value=True)
        self.bot.feature_retweets()
        self.assertEqual(4, self.bot.twitter.retweet.call_count)
