'''
RobotTestCaste RobotTest
'''

import os
import tempfile

from unittest import mock
from unittest import TestCase
from unittest.mock import patch

from karlsruher.brain import Brain
from karlsruher.karlsruher import Karlsruher, read_mentions, retweet_mentions


## Static test data:
test_home = tempfile.gettempdir()

user_me = mock.Mock(id=111, screen_name='TestRobot')
user_unknown = mock.Mock(id=777, screen_name='anyone')
advisor_1 = mock.Mock(id=501, screen_name='advisor_1')
advisor_2 = mock.Mock(id=502, screen_name='advisor_2')
advisors = [advisor_1, advisor_2]
follower_1 = mock.Mock(id=101, screen_name='follower_1')
follower_2 = mock.Mock(id=102, screen_name='follower_2')
follower_3 = mock.Mock(id=103, screen_name='follower_3', protected=True)
follower_ids = [follower_1.id, follower_2.id, follower_3.id]
friend_1 = mock.Mock(id=201, screen_name='friend_1')
friend_2 = mock.Mock(id=202, screen_name='friend_2')
friend_ids = [friend_1.id, friend_2.id]

mention_text = 'Test @{} mention.'.format(user_me.screen_name)

tweet_by_nonfollower = mock.Mock(id=1234567890, user=user_unknown, text=mention_text, in_reply_to_status_id=None, )
tweet_by_myself = mock.Mock(id=1234567891, user=user_me, text=mention_text, in_reply_to_status_id=None)
tweet_by_follower_1 = mock.Mock(id=1234567892, user=follower_1, text=mention_text, in_reply_to_status_id=None)
tweet_by_follower_2 = mock.Mock(id=1234567893, user=follower_2, text=mention_text, in_reply_to_status_id=None)
tweet_by_protected_follower = mock.Mock(id=1234567894, user=follower_3, text=mention_text, in_reply_to_status_id=None)
tweet_reply_by_follower = mock.Mock(id=1234567895, user=follower_1, text=mention_text, in_reply_to_status_id=1234567890)
tweet_advise_stop = mock.Mock(id=1234567896, user=advisor_1, text='@{}!STOP!1!'.format(user_me.screen_name), in_reply_to_status_id=None)
tweet_advise_start = mock.Mock(id=1234567897, user=advisor_2, text='@{}! START'.format(user_me.screen_name), in_reply_to_status_id=None)
tweet_advise_unknown = mock.Mock(id=1234567898, user=advisor_1, text='@{}! NOADVISE'.format(user_me.screen_name), in_reply_to_status_id=None)

tweets = [
    tweet_by_nonfollower,
    tweet_by_follower_1,
    tweet_advise_stop,
    tweet_by_follower_2,
    tweet_advise_unknown,
    tweet_advise_start,
    tweet_advise_start,
    tweet_by_myself,
    tweet_by_protected_follower,
    tweet_reply_by_follower
]

##


class KarlsruherTest(TestCase):

    def setUp(self):

        self.api_mock = mock.Mock(
            me=mock.MagicMock(return_value=user_me),
            list_members=mock.MagicMock(return_value=advisors),
            follower_ids=mock.MagicMock(return_value=follower_ids),
            friend_ids=mock.MagicMock(return_value=friend_ids),
            update_status=mock.Mock(),
            retweet=mock.Mock(),
            mentions_timeline=mock.MagicMock(return_value=tweets),
        )

        self.bot = Karlsruher(test_home, Brain(), self.api_mock)
        self.bot.delay = 0

    def tearDown(self):
        if self.bot and os.path.isfile(self.bot.lockfile):
            os.remove(self.bot.lockfile)


    def test_requires_home_directory(self):
        '''Must fail without home'''
        self.assertRaises(NotADirectoryError, Karlsruher)

    def test_requires_existing_home_directory(self):
        '''Must fail with non-existing home'''
        self.assertRaises(NotADirectoryError, Karlsruher, '/not/existing/home')

    @patch('sys.argv', ['--home=' + test_home])
    def test_can_accept_home_directory_from_commandline(self):
        '''Must accept home from commandline'''
        self.bot = None
        bot = Karlsruher(brain=Brain(), api=self.api_mock)
        self.assertTrue(os.path.isfile(bot.lockfile))

    def test_can_lock(self):
        '''Must fail with non-existing home'''
        self.assertRaises(RuntimeError, Karlsruher, test_home)

    def test_can_del(self):
        lockfile = self.bot.lockfile
        self.bot = None
        self.assertFalse(os.path.isfile(lockfile))

    def test_can_repr(self):
        self.assertIn('Hello', str(self.bot))

    def test_can_fetch_advisors(self):
        self.assertTrue(self.bot.brain.has('advisor', advisor_1.id))
        self.assertTrue(self.bot.brain.has('advisor', advisor_2.id))

    def test_can_apply_advises(self):
        self.assertFalse(self.bot.apply_advise(tweet_advise_unknown))
        self.assertFalse(self.bot.is_sleeping())
        self.assertTrue(self.bot.apply_advise(tweet_advise_stop))
        self.assertTrue(self.bot.apply_advise(tweet_advise_stop))
        self.assertTrue(self.bot.is_sleeping())
        self.assertTrue(self.bot.apply_advise(tweet_advise_start))
        self.assertFalse(self.bot.is_sleeping())
        self.assertEqual(3, self.bot.api.update_status.call_count)

    @patch('tweepy.Cursor.items', mock.Mock(side_effect=[follower_ids, friend_ids]))
    def test_can_do_housekeeping(self):
        self.bot.housekeeping()
        self.assertTrue(self.bot.brain.has('follower', follower_1.id))
        self.assertTrue(self.bot.brain.has('follower', follower_2.id))
        self.assertTrue(self.bot.brain.has('follower', follower_3.id))
        self.assertTrue(self.bot.brain.has('friend', friend_1.id))
        self.assertTrue(self.bot.brain.has('friend', friend_2.id))

    @patch('tweepy.Cursor.items', mock.Mock(side_effect=[follower_ids, friend_ids]))
    #@patch('tweepy.API.mentions_timeline', mock.Mock(side_effect=tweets))
    def test_can_read_latest_mentions(self):
        '''Retweet mention by non-protected followers, when mention is not a reply'''
        latest_mentions = self.bot.latest_mentions()
        self.assertEqual(6, len(latest_mentions))
        self.assertNotIn(tweet_by_myself, latest_mentions)
        self.assertNotIn(tweet_advise_start, latest_mentions)
        self.assertNotIn(tweet_advise_stop, latest_mentions)
        self.assertIn(tweet_by_follower_1, latest_mentions)
        self.assertIn(tweet_by_follower_2, latest_mentions)
        self.assertIn(tweet_by_nonfollower, latest_mentions)
        self.assertIn(tweet_by_protected_follower, latest_mentions)
        self.assertIn(tweet_reply_by_follower, latest_mentions)
        self.assertIn(tweet_advise_unknown, latest_mentions)

    @patch('tweepy.Cursor.items', mock.Mock(side_effect=[follower_ids, friend_ids]))
    def test_can_read_mentions(self):
        '''Must retweet mentions'''
        self.bot.housekeeping()
        self.assertEqual(0, self.bot.api.retweet.call_count)
        read_mentions(self.bot)
        self.assertEqual(0, len(self.bot.latest_mentions()))

    @patch('tweepy.Cursor.items', mock.Mock(side_effect=[follower_ids, friend_ids]))
    def test_can_retweet_mentions(self):
        '''Must retweet mentions'''
        self.bot.housekeeping()
        self.assertEqual(0, self.bot.api.retweet.call_count)
        retweet_mentions(self.bot)
        self.assertEqual(2, self.bot.api.retweet.call_count)
        self.assertEqual(0, len(self.bot.latest_mentions()))

    @patch('tweepy.Cursor.items', mock.Mock(side_effect=[follower_ids, friend_ids]))
    def test_can_retweet_mentions_sleeping(self):
        '''Must retweet mentions'''
        self.bot.housekeeping()
        self.bot.latest_mentions()
        self.assertEqual(0, self.bot.api.retweet.call_count)
        self.bot.go_sleep('test')
        self.assertTrue(self.bot.is_sleeping())
        retweet_mentions(self.bot)
        self.assertEqual(0, self.bot.api.retweet.call_count)
        self.assertEqual(0, len(self.bot.latest_mentions()))
