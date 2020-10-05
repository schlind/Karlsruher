'''
RobotTestCaste RobotTest
'''

import tempfile
from unittest import mock
from unittest import TestCase

from karlsruher.common import LockException
from karlsruher.brain import Brain
from karlsruher.robot import Robot
from karlsruher.twitter import TwitterException

class RobotTestCase(TestCase):
    '''TestCase for Robot'''

    def setUp(self):

        self.test_home = tempfile.gettempdir()
        self.test_brain = Brain(':memory:')

        self.user_me = mock.Mock(id=111, screen_name='TestRobot')
        self.user_unknown = mock.Mock(id=777, screen_name='anyone')

        self.advisor_1 = mock.Mock(id=501, screen_name='advisor_1')
        self.advisor_2 = mock.Mock(id=502, screen_name='advisor_2')

        self.follower_1 = mock.Mock(id=101, screen_name='follower_1')
        self.follower_2 = mock.Mock(id=102, screen_name='follower_2')
        self.follower_3 = mock.Mock(id=103, screen_name='follower_3', protected=True)

        self.friend_1 = mock.Mock(id=201, screen_name='friend_1')
        self.friend_2 = mock.Mock(id=202, screen_name='friend_2')

        self.mention_text = 'Test @{} mention.'.format(self.user_me.screen_name)

        self.tweet_from_nonfollower = mock.Mock(
            id=1234567890,
            user=self.user_unknown,
            text=self.mention_text,
            in_reply_to_status_id=None,
        )
        self.tweet_by_myself = mock.Mock(
            id=1234567891,
            user=self.user_me,
            text=self.mention_text,
            in_reply_to_status_id=None,
        )
        self.tweet_by_follower_1 = mock.Mock(
            id=1234567892,
            user=self.follower_1,
            text=self.mention_text,
            in_reply_to_status_id=None,
        )
        self.tweet_by_follower_2 = mock.Mock(
            id=1234567893,
            user=self.follower_2,
            text=self.mention_text,
            in_reply_to_status_id=None,
        )
        self.tweet_by_protected_follower = mock.Mock(
            id=1234567894,
            user=self.follower_3,
            text=self.mention_text,
            in_reply_to_status_id=None,
        )
        self.tweet_reply_by_follower = mock.Mock(
            id=1234567895,
            user=self.follower_1,
            text=self.mention_text,
            in_reply_to_status_id=1234567890,
        )
        self.tweet_advise_stop = mock.Mock(
            id=1234567896,
            user=self.advisor_1,
            text='@{}!STOP!1!'.format(self.user_me.screen_name),
            in_reply_to_status_id=None,
        )
        self.tweet_advise_start = mock.Mock(
            id=1234567897,
            user=self.advisor_2,
            text='@{}! START'.format(self.user_me.screen_name),
            in_reply_to_status_id=None,
        )
        self.tweet_advise_unknown = mock.Mock(
            id=1234567898,
            user=self.advisor_1,
            text='@{}! NOADVISE'.format(self.user_me.screen_name),
            in_reply_to_status_id=None,
        )
        self.tweet_advise_not_an_advise = mock.Mock(
            id=1234567899,
            user=self.advisor_2,
            text='Not an advise, hello @{}!'.format(self.user_me.screen_name),
            in_reply_to_status_id=None,
        )


        self.mock_twitter = mock.Mock(
            me=mock.MagicMock(return_value=self.user_me),
            list_members=mock.MagicMock(return_value=[self.advisor_1, self.advisor_2]),
            follower_ids=mock.MagicMock(return_value=[self.follower_1.id, self.follower_2.id, self.follower_3.id]),
            friend_ids=mock.MagicMock(return_value=[self.friend_1.id, self.friend_2.id]),
            update_status=mock.Mock(),
            retweet=mock.Mock(),
            mentions_timeline=mock.MagicMock(return_value=[
                # 1 read_mention 1
                self.tweet_from_nonfollower,
                # 2 retweet_action 1
                self.tweet_by_follower_1,
                # 3 advise_action 1
                self.tweet_advise_stop,
                # 4 read_mention 2 (sleeping)
                self.tweet_by_follower_2,
                # 5 read_mention 3
                self.tweet_advise_not_an_advise,
                # 6 read_mention 4
                self.tweet_advise_unknown,
                # 7 advise_action 2
                self.tweet_advise_start,
                #8 ...
                self.tweet_advise_start,
                # 9 totally ignored
                self.tweet_by_myself,
                # 10 read_mention 5
                self.tweet_by_protected_follower,
                # 11 read_mention 6
                self.tweet_reply_by_follower
            ]),
        )

        self.mock_twitter.screen_name = self.mock_twitter.me().screen_name
        self.bot = None

    def tearDown(self):
        if self.bot is not None:
            # Just to be sure:
            self.bot.lock.release()
            self.bot.sleep.release()



class RobotTest(RobotTestCase):
    '''Test the Robot'''

    def setUp(self):
        '''Create a Robot'''
        super().setUp()
        self.bot = Robot(self.test_home, self.test_brain, self.mock_twitter)

    def test_is_not_locked_initially(self):
        '''Must not be locked'''
        self.assertFalse(self.bot.lock.is_acquired())
        self.assertFalse(self.bot.sleep.is_acquired())

    def test_can_detect_sleeping_mode(self):
        '''Must detect sleep-mode'''
        self.bot.go_sleep()
        new_bot = Robot(self.test_home, self.test_brain, self.mock_twitter)
        self.assertFalse(new_bot.is_awake())

    def test_requires_existing_home_directory(self):
        '''Must fail with non-existing home'''
        self.assertRaises(NotADirectoryError, Robot, './not/existing/home')

    def test_act_on_twitter_default(self):
        '''Must act on Twitter'''
        self.assertTrue(self.bot.act_on_twitter)

    def test_can_get_screen_name(self):
        '''Must determine own name'''
        self.assertEqual(self.user_me.screen_name, self.bot.twitter.screen_name)
        self.assertEqual(1, self.bot.twitter.me.call_count)

    def test_can_handle_sleep_mode(self):
        '''Must handle sleep mode'''
        self.assertTrue(self.bot.is_awake())
        self.bot.go_sleep('test')
        self.assertFalse(self.bot.is_awake())
        self.bot.go_sleep('test')
        self.bot.wake_up('test')
        self.assertTrue(self.bot.is_awake())

    def test_has_advisors(self):
        '''Must have advisors'''
        self.assertEqual(2, len(self.bot.advisors))
        self.assertTrue('501' in self.bot.advisors)
        self.assertTrue('502' in self.bot.advisors)

    def test_can_apply_advises(self):
        '''Must apply advises'''
        self.assertTrue(self.bot.is_awake())
        self.assertTrue(self.bot.apply_advise(self.tweet_advise_stop))
        self.assertFalse(self.bot.is_awake())
        self.assertTrue(self.bot.apply_advise(self.tweet_advise_start))
        self.assertTrue(self.bot.is_awake())
        self.assertFalse(self.bot.apply_advise(self.tweet_advise_not_an_advise))
        self.assertFalse(self.bot.apply_advise(self.tweet_advise_unknown))
        self.assertFalse(self.bot.apply_advise(self.tweet_by_follower_1))

    def test_can_apply_advises_once_only(self):
        '''Must apply advises once only'''
        self.bot.get_new_mentions()
        self.bot.get_new_mentions()
        self.bot.get_new_mentions()
        self.assertEqual(2, self.bot.twitter.update_status.call_count)

    def test_housekeeping(self):
        '''Must do proper housekeeping'''
        self.bot.housekeeping()
        self.assertTrue(self.bot.is_follower("101"))
        self.assertTrue(self.bot.is_follower("102"))
        self.assertTrue(self.bot.is_follower("103"))
        self.assertTrue(self.bot.is_friend("201"))
        self.assertTrue(self.bot.is_friend("202"))

    def test_housekeeping_handles_lock(self):
        '''Must not ignore housekeeping lock'''
        self.bot.lock.acquire()
        self.assertRaises(LockException, self.bot.housekeeping)

    def test_can_handle_tweets(self):
        '''Must handle tweets'''
        self.assertFalse(self.bot.has_tweet(123))
        self.bot.remember_tweet(123)
        self.assertTrue(self.bot.has_tweet(123))
        self.assertEqual('@follower_1/1234567892', Robot.tweet_str(self.tweet_by_follower_1))

    def test_can_tweet(self):
        '''Must tweet'''
        self.bot.act_on_twitter = False
        self.bot.tweet('Hello!')
        self.assertEqual(0, self.bot.twitter.update_status.call_count)
        self.bot.act_on_twitter = True
        self.bot.tweet('Hello!')
        self.assertEqual(1, self.bot.twitter.update_status.call_count)

    def test_can_build_reply_status(self):
        '''Must build reply status'''
        user_name = self.tweet_advise_unknown.user.screen_name
        good_reply = 'Already mention @' + user_name + ' in reply.'
        self.assertEqual(
            good_reply,
             self.bot.build_reply_status(self.tweet_advise_unknown, good_reply)
        )
        fix_reply = 'Does not mention anything.'
        self.assertEqual(
            '@' + user_name + ' ' + fix_reply,
             self.bot.build_reply_status(self.tweet_advise_unknown, fix_reply)
        )

    def test_can_reply(self):
        '''Must reply'''
        self.bot.act_on_twitter = False
        self.bot.reply(self.tweet_advise_unknown, 'Nope!')
        self.assertEqual(0, self.bot.twitter.update_status.call_count)
        self.bot.act_on_twitter = True
        self.bot.reply(self.tweet_advise_unknown, 'Nope!')
        self.assertEqual(1, self.bot.twitter.update_status.call_count)

    def test_get_new_mentions(self):
        '''Must provide new mentions'''
        mentions = self.bot.get_new_mentions()
        self.assertEqual(7, len(mentions))
        self.bot.remember_tweet(mentions[0].id)
        self.bot.remember_tweet(mentions[3].id)
        mentions = self.bot.get_new_mentions()
        self.assertEqual(5, len(mentions))

    def test_error_handling_advise(self):
        '''Exceptions must not stop process'''
        self.bot.twitter.update_status = mock.Mock(side_effect=TwitterException('Expect me!'))
        self.assertTrue(self.bot.apply_advise(self.tweet_advise_stop))
        self.assertTrue(self.bot.apply_advise(self.tweet_advise_start))
        self.assertEqual(2, self.bot.twitter.update_status.call_count)
