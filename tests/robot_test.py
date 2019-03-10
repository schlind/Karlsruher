# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher

"""
"""

import tempfile
from unittest import mock
from unittest import TestCase

from karlsruher.brain import Brain
from karlsruher.common import LockException
from karlsruher.robot import Config, Robot


class ConfigTest(TestCase):

    """Test config."""

    def setUp(self):
        self.test_home = tempfile.gettempdir()

    def test_config_requires_existing_home_directory(self):
        """Config must fail with non-existing home."""
        self.assertRaises(NotADirectoryError, Config, './not/existing/home')

    def test_config_has_home_and_defaults(self):
        """Config must have defaults."""
        config = Config(home=self.test_home)
        self.assertFalse(config.do_reply)
        self.assertFalse(config.do_retweet)
        self.assertEqual(config.home, self.test_home)

    def test_config_has_do_reply(self):
        """Config must take values."""
        config = Config(home=self.test_home, do_reply=True, do_retweet=False)
        self.assertTrue(config.do_reply)
        self.assertFalse(config.do_retweet)

    def test_config_has_do_retweet(self):
        """Config must take values."""
        config = Config(home=self.test_home, do_reply=False, do_retweet=True)
        self.assertFalse(config.do_reply)
        self.assertTrue(config.do_retweet)


class RobotTestCase(TestCase):

    """Provide re-usable test data and mocks."""

    def setUp(self):

        self.test_home = tempfile.gettempdir()
        self.test_config = Config(home=self.test_home)
        self.test_brain = Brain(':memory:')

        self.mock_me = mock.Mock(id=111, screen_name='TestBot')
        self.mention_text = 'Test @{} mention.'.format(self.mock_me.screen_name)

        self.mock_anyuser = mock.Mock(id=777, screen_name='any_user')
        self.mock_follower_1 = mock.Mock(id=101, screen_name='follower_1')
        self.mock_follower_2 = mock.Mock(id=102, screen_name='follower_2')
        self.mock_follower_3 = mock.Mock(id=103, screen_name='follower_3', protected=True)
        self.mock_friend_1 = mock.Mock(id=201, screen_name='friend_1')
        self.mock_friend_2 = mock.Mock(id=202, screen_name='friend_2')
        self.mock_advisor_1 = mock.Mock(id=501, screen_name='advisor_1')
        self.mock_advisor_2 = mock.Mock(id=502, screen_name='advisor_2')

        self.mock_mention_from_nonfollower = mock.Mock(
            in_reply_to_status_id=None, id=1346453345, user=self.mock_anyuser,
            text=self.mention_text
        )
        self.mock_mention_by_myself = mock.Mock(
            in_reply_to_status_id=None, id=69823745, user=self.mock_me,
            text=self.mention_text
        )
        self.mock_mention_by_follower_1 = mock.Mock(
            in_reply_to_status_id=None, id=7239847976, user=self.mock_follower_1,
            text=self.mention_text
        )
        self.mock_mention_by_follower_2 = mock.Mock(
            in_reply_to_status_id=None, id=892346197, user=self.mock_follower_2,
            text=self.mention_text
        )
        self.mock_mention_by_protected_follower = mock.Mock(
            in_reply_to_status_id=None, id=937091748, user=self.mock_follower_3,
            text=self.mention_text
        )
        self.mock_mention_reply_by_follower = mock.Mock(
            in_reply_to_status_id=9237498712, id=34993409, user=self.mock_follower_1,
            text=self.mention_text
        )
        self.mock_mention_advice_gosleep = mock.Mock(
            in_reply_to_status_id=None, id=2345345345, user=self.mock_advisor_1,
            text='@{}! geh schlafen!'.format(self.mock_me.screen_name)
        )
        self.mock_mention_advice_wakeup = mock.Mock(
            in_reply_to_status_id=None, id=33453453, user=self.mock_advisor_2,
            text='@{}! wach auf!'.format(self.mock_me.screen_name)
        )
        self.mock_mention_advice_unknown = mock.Mock(
            in_reply_to_status_id=None, id=4987349587, user=self.mock_advisor_1,
            text='@{}! foo bar!'.format(self.mock_me.screen_name)
        )
        self.mock_mention_advice_not_an_advice = mock.Mock(
            in_reply_to_status_id=None, id=5829347, user=self.mock_advisor_2,
            text='not an advice @{} hi!'.format(self.mock_me.screen_name)
        )

        self.mock_twitter = mock.Mock(
            me=mock.MagicMock(return_value=self.mock_me),
            followers=mock.MagicMock(return_value=[
                self.mock_follower_1,
                self.mock_follower_2,
                self.mock_follower_3
            ]),
            friends=mock.MagicMock(return_value=[
                self.mock_friend_1,
                self.mock_friend_2
            ]),
            list_members=mock.MagicMock(return_value=[
                self.mock_advisor_1,
                self.mock_advisor_2
            ]),
            update_status=mock.Mock(),
            retweet=mock.Mock(),
            mentions_timeline=mock.MagicMock(return_value=[
                # 1 read_mention 1
                self.mock_mention_from_nonfollower,
                # 2 retweet_action 1
                self.mock_mention_by_follower_1,
                # 3 advice_action 1
                self.mock_mention_advice_gosleep,
                # 4 read_mention 2 (sleeping)
                self.mock_mention_by_follower_2,
                # 5 read_mention 3
                self.mock_mention_advice_not_an_advice,
                # 6 read_mention 4
                self.mock_mention_advice_unknown,
                # 7 advice_action 2
                self.mock_mention_advice_wakeup,
                # totally ignored
                self.mock_mention_by_myself,
                # 8 read_mention 5
                self.mock_mention_by_protected_follower,
                # 9 read_mention 6
                self.mock_mention_reply_by_follower
            ]),
        )

        self.mock_twitter.screen_name = self.mock_twitter.me().screen_name
        self.bot = None

    def tearDown(self):
        if self.bot is not None:
            # Just to be sure:
            self.bot.lock.release()


class RobotTest(RobotTestCase):

    """Test basics."""

    def setUp(self):
        super().setUp()
        self.bot = Robot(
            config=self.test_config,
            brain=self.test_brain,
            twitter=self.mock_twitter
        )

    def test_robot_is_not_locked(self):
        """The bot should not be locked."""
        self.assertFalse(self.bot.lock.is_acquired())

    def test_robot_performs(self):
        """The bot should perform."""
        self.assertTrue(callable(self.bot.perform))
        self.bot.perform()

    def test_robot_can_get_screen_name(self):
        """The bot should determine it's name."""
        self.assertEqual(self.mock_me.screen_name, self.bot.twitter.screen_name)
        self.assertEqual(1, self.bot.twitter.me.call_count)

    def test_robot_starts_with_empty_brain(self):
        """The bot's brain should be empty."""
        self.assertEqual(0, self.bot.brain.count_tweets())
        self.assertEqual(0, len(self.bot.brain.users('follower')))
        self.assertEqual(0, len(self.bot.brain.users('friend')))
        self.assertIsNone(self.bot.brain.get('retweet.disabled'))

    def test_robot_does_create_brain(self):
        """The bot should create a brain."""
        bot = Robot(config=self.test_config, twitter=self.mock_twitter)
        self.assertEqual(Brain, bot.brain.__class__)

    def test_reply_off(self):
        """The bot must not reply."""
        self.bot.reply(mock.Mock(id=1), 'test')
        self.assertEqual(0, self.bot.twitter.update_status.call_count)

    def test_reply_on(self):
        """The bot must reply."""
        self.bot.config.do_reply = True
        self.bot.reply(mock.Mock(id=1), 'test')
        self.assertEqual(1, self.bot.twitter.update_status.call_count)

    def test_retweet_off(self):
        """The bot must not retweet."""
        self.bot.retweet(mock.Mock(id=1))
        self.assertEqual(0, self.bot.twitter.retweet.call_count)

    def test_retweet_on(self):
        """The bot must retweet."""
        self.bot.config.do_retweet = True
        self.bot.retweet(mock.Mock(id=1))
        self.assertEqual(1, self.bot.twitter.retweet.call_count)
