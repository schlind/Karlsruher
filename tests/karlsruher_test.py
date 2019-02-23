'''
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher
'''

import contextlib
import io
import os
import sys
import tempfile
from unittest import mock
from unittest import TestCase

import karlsruher


class KarlsruherTest(TestCase):

    def setUp(self):
        self.home = tempfile.gettempdir()
        self.brain = karlsruher.Brain(':memory:')
        self.me = mock.Mock(id = 12345678900, screen_name = 'MockBot')
        self.advisor = mock.Mock(id = 750000, screen_name = 'advisor')
        self.follower = mock.Mock(id = 54321, screen_name = 'follower')
        self.friend = mock.Mock(id = 1111111, screen_name = 'friend')
        self.unknown = mock.Mock(id = 700007, screen_name = 'unknown')
        self.mentionText = 'Test @{} mention.'.format(self.me.screen_name)
        self.tweet = mock.Mock(
            in_reply_to_status_id = None,
            id = 721721721,
            user = self.unknown,
            text = self.mentionText
        )
        self.twitter = mock.Mock(
            me = mock.MagicMock(return_value = self.me),
            list_advisors = mock.MagicMock(return_value = [self.advisor]),
            followers = mock.MagicMock(return_value = [self.follower,self.advisor]),
            friends = mock.MagicMock(return_value = [self.friend]),
            update_status = mock.Mock(),
            retweet = mock.Mock(),
            mentions_timeline = mock.MagicMock(return_value = [
                self.tweet,
                mock.Mock( ## should be an advice
                    in_reply_to_status_id = None,
                    id = 1111111111,
                    user = self.advisor,
                    text = '@' + self.me.screen_name + '! geh schlafen!'
                ),
                mock.Mock( ## should be an advice
                    in_reply_to_status_id = None,
                    id = 2222222222,
                    user = self.advisor,
                    text = '@' + self.me.screen_name + '! wach auf!'
                ),
                mock.Mock( ## should be retweeted
                    in_reply_to_status_id = None,
                    id = 3333333333,
                    user = self.follower,
                    text = self.mentionText
                ),
                mock.Mock( ## should be retweeted
                    in_reply_to_status_id = None,
                    id = 4444444444,
                    user = self.follower,
                    text = self.mentionText
                )
            ]),
        )
        self.bot = karlsruher.Karlsruher(
            config = karlsruher.Config(home=self.home),
            brain = self.brain,
            twitter = self.twitter
        )

    def tearDown(self):
        self.bot.lock.release()

    def test_require_home_directory(self):
        self.assertRaises(Exception, karlsruher.Karlsruher, '/not/existing')

    def test_brain_create(self):
        bot = karlsruher.Karlsruher(
            config=karlsruher.Config(home=self.home),
            twitter=self.twitter
        )
        self.assertTrue(bot.brain.__class__)

    def test_not_locked(self):
        self.assertFalse(self.bot.lock.is_present())

    def test_init_can_get_me(self):
        self.assertEqual(self.bot.screen_name, self.me.screen_name)
        self.assertEqual(1, self.bot.twitter.me.call_count)

    def test_init_can_load_advisors(self):
        self.assertEqual(1, self.bot.twitter.list_advisors.call_count)
        self.assertEqual(1, len(self.bot.brain.advisors))
        self.assertTrue(str(self.advisor.id) in self.bot.brain.advisors)
        self.assertFalse(str(self.unknown.id) in self.bot.brain.advisors)

    def test_empty_brain(self):
        self.assertEqual(0, self.bot.brain.count_tweets())
        self.assertEqual(0, len(self.bot.brain.users('followers')))
        self.assertEqual(0, len(self.bot.brain.users('friends')))
        self.assertIsNone(self.bot.brain.get_value('retweet.disabled'))

    def test_housekeeping_not_when_locked(self):
        self.bot.lock.acquire()
        self.assertRaises(karlsruher.common.LockException, self.bot.house_keeping)

    def test_housekeeping(self):
        self.bot.house_keeping()
        self.assertEqual(2, len(self.bot.brain.users('followers')))
        self.assertEqual(1, len(self.bot.brain.users('friends')))

    def test_read_mention(self):
        self.assertTrue(self.bot.read_mention(self.tweet))

    def test_read_mention_only_once(self):
        self.assertTrue(self.bot.read_mention(self.tweet))
        self.assertFalse(self.bot.read_mention(self.tweet))

    def test_read_mentions_not_when_locked(self):
        self.bot.lock.acquire()
        self.assertRaises(karlsruher.common.LockException, self.bot.read_mentions)
        self.assertEqual(0, self.bot.brain.count_tweets())
        self.assertEqual(0, self.bot.twitter.update_status.call_count)
        self.assertEqual(0, self.bot.twitter.retweet.call_count)

    def test_read_mentions_delegate_advice(self):
        self.bot.config.do_reply = True
        self.bot.read_mentions()
        self.assertEqual(5, self.bot.brain.count_tweets())
        self.assertEqual(2, self.bot.twitter.update_status.call_count)
        self.assertEqual(0, self.bot.twitter.retweet.call_count)

    def test_read_mentions_delegate_retweet(self):
        self.bot.config.do_retweet = True
        self.bot.house_keeping()
        self.bot.read_mentions()
        self.assertEqual(0, self.bot.twitter.update_status.call_count)
        self.assertEqual(2, self.bot.twitter.retweet.call_count)

    def test_advice_can_ignore_from_non_advisors(self):
        self.tweet.text = '@{}! gEh scHlafen!!!'.format(self.me.screen_name)
        self.assertFalse(self.bot.advice_action(self.tweet))

    def test_advice_can_accept_sleep(self):
        self.tweet.text = '@{}! gEh scHlafen!!!'.format(self.me.screen_name)
        self.tweet.user = self.advisor
        self.bot.config.do_reply = True
        self.assertTrue(self.bot.advice_action(self.tweet))
        self.assertTrue(self.bot.brain.get_value('retweet.disabled'))
        self.assertEqual(1, self.bot.twitter.update_status.call_count)

    def test_advice_can_accept_wakeup(self):
        self.tweet.text = '@{}! waCh auf!!!'.format(self.me.screen_name)
        self.tweet.user = self.advisor
        self.bot.config.do_reply = False
        self.bot.brain.set_value('retweet.disabled', True)
        self.assertTrue(self.bot.advice_action(self.tweet))
        self.assertIsNone(self.bot.brain.get_value('retweet.disabled'))
        self.assertEqual(0, self.bot.twitter.update_status.call_count)

    def test_advice_not_given_by_advisor(self):
        self.tweet.text = '@{} not an advice'.format(self.me.screen_name)
        self.tweet.user = self.advisor
        self.assertFalse(self.bot.advice_action(self.tweet))

    def test_advice_unrecognized_by_advisor(self):
        self.tweet.text = '@{}! unrecognized advice'.format(self.me.screen_name)
        self.tweet.user = self.advisor
        self.assertFalse(self.bot.advice_action(self.tweet))

    def test_retweet_not_during_sleep(self):
        self.bot.house_keeping()
        self.bot.config.do_retweet = True
        self.tweet.user = self.follower
        self.bot.brain.set_value('retweet.disabled', True)
        self.assertFalse(self.bot.retweet_action(self.tweet))
        self.assertEqual(0, self.bot.twitter.retweet.call_count)

    def test_retweet_not_myself(self):
        self.bot.house_keeping()
        self.bot.config.do_retweet = True
        self.tweet.user = self.me
        self.assertFalse(self.bot.retweet_action(self.tweet))
        self.assertEqual(0, self.bot.twitter.retweet.call_count)

    def test_retweet_not_protected(self):
        self.bot.house_keeping()
        self.bot.config.do_retweet = True
        for user in [
            self.me, self.advisor, self.follower, self.friend, self.unknown
        ]:
            self.tweet.user = user
            self.tweet.user.protected = True
            self.assertFalse(self.bot.retweet_action(self.tweet))
        self.assertEqual(0, self.bot.twitter.retweet.call_count)

    def test_retweet_not_replies(self):
        self.bot.house_keeping()
        self.bot.config.do_retweet = True
        self.tweet.in_reply_to_status_id = 7500
        for user in [
            self.me, self.advisor, self.follower, self.friend, self.unknown
        ]:
            self.tweet.user = user
            self.assertFalse(self.bot.retweet_action(self.tweet))
        self.assertEqual(0, self.bot.twitter.retweet.call_count)

    def test_retweet_not_non_followers(self):
        self.bot.house_keeping()
        self.bot.config.do_retweet = True
        self.assertFalse(self.bot.retweet_action(self.tweet))
        self.assertEqual(0, self.bot.twitter.retweet.call_count)

    def test_retweet_follower(self):
        self.bot.house_keeping()
        self.bot.config.do_retweet = True
        self.tweet.user = self.follower
        self.assertTrue(self.bot.retweet_action(self.tweet))
        self.assertEqual(1, self.bot.twitter.retweet.call_count)

    def test_retweet_not_when_disabled(self):
        self.bot.house_keeping()
        self.bot.config.do_retweet = False
        for user in [self.follower, self.advisor]:
            self.tweet.user = user
            self.assertTrue(self.bot.retweet_action(self.tweet))
        self.assertEqual(0, self.bot.twitter.retweet.call_count)




class BrainTest(TestCase):

    def setUp(self):
        self.user1 = mock.Mock(id = 1, screen_name = 'user1')
        self.user2 = mock.Mock(id = 2, screen_name = 'user2')
        self.user3 = mock.Mock(id = 3, screen_name = 'user3')
        self.brain = karlsruher.Brain(':memory:')

    def test_can_get_default_value(self):
        self.assertEqual('default', self.brain.get_value('test', 'default'))

    def test_can_set_get_string_value(self):
        self.brain.set_value('test', 'string')
        self.assertEqual('string', self.brain.get_value('test'))

    def test_can_set_get_boolean_value_true(self):
        self.brain.set_value('test', True)
        self.assertTrue(self.brain.get_value('test'))

    def test_can_set_get_boolean_value_false(self):
        self.brain.set_value('test', False)
        self.assertFalse(self.brain.get_value('test'))

    def test_can_set_get_value_none_as_false(self):
        self.brain.set_value('test')
        self.assertIsNone(self.brain.get_value('test'))
        self.assertFalse(self.brain.get_value('test'))

    def test_can_count_tweets_empty(self):
        self.assertEqual(0, self.brain.count_tweets())

    def test_can_add_and_have_tweet(self):
        tweet = mock.Mock(id = 111, user = self.user1)
        self.assertFalse(self.brain.has_tweet(tweet))
        self.assertEqual(1, self.brain.add_tweet(tweet, 'test'))
        self.assertTrue(self.brain.has_tweet(tweet))

    def test_not_updating_tweets(self):
        tweet = mock.Mock(id = 111, user = self.user1)
        self.assertFalse(self.brain.has_tweet(tweet))
        self.assertEqual(1, self.brain.add_tweet(tweet, 'test'))
        self.assertEqual(0, self.brain.add_tweet(tweet, 'test'))

    def test_can_count_tweets(self):
        self.brain.add_tweet(mock.Mock(id = 111, user = self.user1), 'test')
        self.brain.add_tweet(mock.Mock(id = 222, user = self.user1), 'test')
        self.assertEqual(2, self.brain.count_tweets())
        self.brain.add_tweet(mock.Mock(id = 333, user = self.user2), 'test')
        self.assertEqual(3, self.brain.count_tweets())

    def test_can_count_tweets_by_reason(self):
        self.brain.add_tweet(mock.Mock(id = 111, user = self.user1), 'A')
        self.brain.add_tweet(mock.Mock(id = 222, user = self.user1), 'B')
        self.brain.add_tweet(mock.Mock(id = 333, user = self.user2), 'A')
        self.assertEqual(2, self.brain.count_tweets(reason = 'A'))
        self.assertEqual(1, self.brain.count_tweets(reason = 'B'))
        self.assertEqual(0, self.brain.count_tweets(reason = '?'))

    def test_can_count_tweets_by_screen_name(self):
        self.brain.add_tweet(mock.Mock(id = 111, user = self.user1), 'A')
        self.brain.add_tweet(mock.Mock(id = 222, user = self.user1), 'B')
        self.brain.add_tweet(mock.Mock(id = 333, user = self.user2), 'A')
        self.assertEqual(2, self.brain.count_tweets(user_screen_name = self.user1.screen_name))
        self.assertEqual(1, self.brain.count_tweets(user_screen_name = self.user2.screen_name))
        self.assertEqual(0, self.brain.count_tweets(user_screen_name = '?'))

    def test_can_count_tweets_by_reason_and_screen_name(self):
        self.brain.add_tweet(mock.Mock(id = 111, user = self.user1), 'A')
        self.brain.add_tweet(mock.Mock(id = 222, user = self.user1), 'B')
        self.brain.add_tweet(mock.Mock(id = 333, user = self.user2), 'A')
        self.assertEqual(1, self.brain.count_tweets(reason = 'A', user_screen_name = self.user1.screen_name))
        self.assertEqual(1, self.brain.count_tweets(reason = 'B', user_screen_name = self.user1.screen_name))
        self.assertEqual(1, self.brain.count_tweets(reason = 'A', user_screen_name = self.user2.screen_name))
        self.assertEqual(0, self.brain.count_tweets(reason = '?', user_screen_name = '?'))

    def test_can_add_and_has_user(self):
        for table in ['followers', 'friends']:
            self.assertFalse(self.brain.has_user(table, self.user3.id))
            self.assertEqual(1, self.brain.add_user(table, self.user3))
            self.assertTrue(self.brain.has_user(table, self.user3.id))

    def __user_stream(self):
        for user in [ self.user1, self.user2, self.user3 ]:
            yield user

    def test_can_handle_users_stream(self):
        for table in ['followers', 'friends']:
            self.brain.import_users(table , self.__user_stream)
            self.assertEqual(3, len(self.brain.users(table)))

    def test_can_handle_users_array(self):
        for table in ['followers', 'friends']:
            self.brain.import_users(table , self.__user_stream())
            self.assertEqual(3, len(self.brain.users(table)))

    def test_can_handle_advisors_stream(self):
        self.brain.memorize_advisors(self.__user_stream)
        self.assertEqual(3, len(self.brain.advisors))

    def test_can_handle_advisors_array(self):
        self.brain.memorize_advisors(self.__user_stream())
        self.assertEqual(3, len(self.brain.advisors))

    def test_metrics_complete(self):
        metrics = self.brain.metrics()
        self.assertTrue('0' in metrics)
        self.assertTrue('(' in metrics)
        self.assertTrue(')' in metrics)
        self.assertTrue('tweets, ' in metrics)
        self.assertTrue('advisors, ' in metrics)
        self.assertTrue('followers, ' in metrics)
        self.assertTrue('friends, ' in metrics)
        self.assertTrue('config values' in metrics)




class CommandLineTest(TestCase):

    run_commands = ['-housekeeping','-read','-talk']

    def tearDown(self):
        os.environ['KARLSRUHER_HOME'] = 'KARLSRUHER_HOME'

    @contextlib.contextmanager
    def managed_std_streams(self):
        realout, realerr = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
            yield sys.stdout, sys.stderr
        finally:
            sys.stdout, sys.stderr = realout, realerr

    def test_can_show_version(self):
        with self.managed_std_streams() as (out, err):
                sys.argv = ['-v']
                self.assertEqual(0, karlsruher.CommandLine.run())
                console = out.getvalue().strip()
                self.assertTrue(console.startswith('Karlsruher '), console)

    def test_can_show_help(self):
        with self.managed_std_streams() as (out, err):
            for arg in ['','-help','what?']:
                sys.argv = [arg]
                self.assertEqual(0, karlsruher.CommandLine.run())
                console = out.getvalue().strip()
                self.assertTrue(console.startswith('Karlsruher '), console)

    def test_can_show_error_missing_home(self):
        with self.managed_std_streams() as (out, err):
            for arg in self.run_commands:
                sys.argv = [arg]
                self.assertEqual(1, karlsruher.CommandLine.run())
                console = out.getvalue().strip()
                self.assertTrue(console.startswith('Please specify '), console)

    def test_can_show_error_non_existing_home(self):
        with self.managed_std_streams() as (out, err):
            for arg in self.run_commands:
                sys.argv = [arg, '--home=/does/not/exist']
                self.assertEqual(1, karlsruher.CommandLine.run())
                console = out.getvalue().strip()
                self.assertTrue(console.startswith('Specified home '), console)

    def test_can_run_until_credentials_missing(self):
        for arg in self.run_commands:
            with self.managed_std_streams() as (out, err):
                sys.argv = [arg, '--home=' + tempfile.gettempdir()]
                self.assertEqual(1, karlsruher.CommandLine.run())
                console = out.getvalue().strip()
                self.assertTrue(console.startswith('Please create '), console)

    @mock.patch('karlsruher.karlsruher.Twitter')
    def test_can_run(self, twitter_mock):
        for arg in self.run_commands:
            with self.managed_std_streams() as (out, err):
                sys.argv = [arg, '--home=' + tempfile.gettempdir()]
                self.assertEqual(0, karlsruher.CommandLine.run())
                console = out.getvalue().strip()
                self.assertEqual(0, len(console))

    @mock.patch('karlsruher.karlsruher.Twitter')
    def test_can_run_with_KARLSRUHER_HOME(self, twitter_mock):
        original_environ = os.environ
        try:
            os.environ = mock.Mock(get=mock.MagicMock(return_value=tempfile.gettempdir()))
            for arg in self.run_commands:
                with self.managed_std_streams() as (out, err):
                    sys.argv = [arg,]
                    self.assertEqual(0, karlsruher.CommandLine.run())
                    console = out.getvalue().strip()
                    self.assertTrue(console.startswith('Using KARLSRUHER_HOME'), console)
        finally:
            os.environ = original_environ
