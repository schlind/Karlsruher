## Karlsruher Retweet Bot
## https://github.com/schlind/Karlsruher

from unittest import mock, TestCase


from contextlib import contextmanager
from io import StringIO
import sys, tempfile


#from karlsruher.Brain import Brain
#from karlsruher.Karlsruher import Karlsruher
#from karlsruher.CommandLine import CommandLine

import karlsruher

##
##
class KarlsruherTest(TestCase):

	def setUp(self):
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

		self.home = home = tempfile.gettempdir()
		self.brain = karlsruher.Brain(':memory:')
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
			home = self.home,
			brain = self.brain,
			twitter = self.twitter
		)

	def tearDown(self):
		self.bot.lock.release()


	def test_000_require_home_directory(self):
		self.assertRaises(Exception, karlsruher.Karlsruher, '/not/existing/directory')

	def test_000_brain_create(self):
		bot = karlsruher.Karlsruher(
			home = self.home,
			twitter = self.twitter
		)
		self.assertTrue(bot.brain.__class__)


	def test_001_not_locked(self):
		self.assertFalse(self.bot.lock.is_present())

	def test_101_init_can_get_me(self):
		self.assertEqual(self.bot.screen_name, self.me.screen_name)
		self.assertEqual(1, self.bot.twitter.me.call_count)

	def test_102_init_can_load_advisors(self):
		self.assertEqual(1, self.bot.twitter.list_advisors.call_count)
		self.assertEqual(1, len(self.bot.advisors))
		self.assertTrue(str(self.advisor.id) in self.bot.advisors)
		self.assertFalse(str(self.unknown.id) in self.bot.advisors)


	def test_201_empty_brain(self):
		self.assertEqual(0, self.bot.brain.count_tweets())
		self.assertEqual(0, len(self.bot.brain.users('followers')))
		self.assertEqual(0, len(self.bot.brain.users('friends')))
		self.assertIsNone(self.bot.brain.get_value('retweet.disabled'))


	def test_301_housekeeping_not_when_locked(self):
		self.assertTrue(self.bot.lock.acquire())
		self.assertFalse(self.bot.house_keeping())

	def test_302_housekeeping(self):
		self.bot.house_keeping()
		self.assertEqual(2, len(self.bot.brain.users('followers')))
		self.assertEqual(1, len(self.bot.brain.users('friends')))


	def test_401_read_mention(self):
		self.assertTrue(self.bot.read_mention(self.tweet))

	def test_402_read_mention_only_once(self):
		self.assertTrue(self.bot.read_mention(self.tweet))
		self.assertFalse(self.bot.read_mention(self.tweet))


	def test_501_read_mentions_not_when_locked(self):
		self.assertTrue(self.bot.lock.acquire())
		self.assertFalse(self.bot.read_mentions())
		self.assertEqual(0, self.bot.brain.count_tweets())
		self.assertEqual(0, self.bot.twitter.update_status.call_count)
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_502_read_mentions_delegate_advice(self):
		self.bot.do_reply = True
		self.assertTrue(self.bot.read_mentions())
		self.assertEqual(5, self.bot.brain.count_tweets())
		self.assertEqual(2, self.bot.twitter.update_status.call_count)
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_503_read_mentions_delegate_retweet(self):
		self.bot.do_retweet = True
		self.bot.house_keeping()
		self.assertTrue(self.bot.read_mentions())
		self.assertEqual(0, self.bot.twitter.update_status.call_count)
		self.assertEqual(2, self.bot.twitter.retweet.call_count)




	def test_601_advice_can_ignore_from_non_advisors(self):
		self.tweet.text = '@{}! gEh scHlafen!!!'.format(self.me.screen_name)
		self.assertFalse(self.bot.advice_action(self.tweet))

	def test_602_advice_can_accept_sleep(self):
		self.tweet.text = '@{}! gEh scHlafen!!!'.format(self.me.screen_name)
		self.tweet.user = self.advisor
		self.bot.do_reply = True
		self.assertTrue(self.bot.advice_action(self.tweet))
		self.assertTrue(self.bot.brain.get_value('retweet.disabled'))
		self.assertEqual(1, self.bot.twitter.update_status.call_count)

	def test_603_advice_can_accept_wakeup(self):
		self.tweet.text = '@{}! waCh auf!!!'.format(self.me.screen_name)
		self.tweet.user = self.advisor
		self.bot.do_reply = False
		self.bot.brain.set_value('retweet.disabled', True)
		self.assertTrue(self.bot.advice_action(self.tweet))
		self.assertIsNone(self.bot.brain.get_value('retweet.disabled'))
		self.assertEqual(0, self.bot.twitter.update_status.call_count)

	def test_604_advice_not_given_by_advisor(self):
		self.tweet.text = '@{} not an advice'.format(self.me.screen_name)
		self.tweet.user = self.advisor
		self.assertFalse(self.bot.advice_action(self.tweet))

	def test_605_advice_unrecognized_by_advisor(self):
		self.tweet.text = '@{}! unrecognized advice'.format(self.me.screen_name)
		self.tweet.user = self.advisor
		self.assertFalse(self.bot.advice_action(self.tweet))


	def test_701_retweet_not_during_sleep(self):
		self.bot.house_keeping()
		self.bot.do_retweet = True
		self.tweet.user = self.follower
		self.bot.brain.set_value('retweet.disabled', True)
		self.assertFalse(self.bot.retweet_action(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_702_retweet_not_myself(self):
		self.bot.house_keeping()
		self.bot.do_retweet = True
		self.tweet.user = self.me
		self.assertFalse(self.bot.retweet_action(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_703_retweet_not_protected(self):
		self.bot.house_keeping()
		self.bot.do_retweet = True
		for user in [
			self.me, self.advisor, self.follower, self.friend, self.unknown
		]:
			self.tweet.user = user
			self.tweet.user.protected = True
			self.assertFalse(self.bot.retweet_action(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_704_retweet_not_replies(self):
		self.bot.house_keeping()
		self.bot.do_retweet = True
		self.tweet.in_reply_to_status_id = 7500
		for user in [
			self.me, self.advisor, self.follower, self.friend, self.unknown
		]:
			self.tweet.user = user
			self.assertFalse(self.bot.retweet_action(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_704_retweet_not_non_followers(self):
		self.bot.house_keeping()
		self.bot.do_retweet = True
		self.assertFalse(self.bot.retweet_action(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_705_retweet_follower(self):
		self.bot.house_keeping()
		self.bot.do_retweet = True
		self.tweet.user = self.follower
		self.assertTrue(self.bot.retweet_action(self.tweet))
		self.assertEqual(1, self.bot.twitter.retweet.call_count)

	def test_706_retweet_not_when_disabled(self):
		self.bot.house_keeping()
		self.bot.do_retweet = False
		for user in [self.follower, self.advisor ]:
			self.tweet.user = user
			self.assertTrue(self.bot.retweet_action(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)





##
##
class BrainTest(TestCase):

	def setUp(self):
		self.user1 = mock.Mock(id = 1, screen_name = 'user1')
		self.user2 = mock.Mock(id = 2, screen_name = 'user2')
		self.user3 = mock.Mock(id = 3, screen_name = 'user3')
		self.brain = karlsruher.Brain(':memory:')

	def test_brain_001_can_get_default_value(self):
		self.assertEqual('default', self.brain.get_value('test', 'default'))

	def test_brain_002_can_set_get_string_value(self):
		self.brain.set_value('test', 'string')
		self.assertEqual('string', self.brain.get_value('test'))

	def test_brain_003_can_set_get_true(self):
		self.brain.set_value('test', True)
		self.assertTrue(self.brain.get_value('test'))

	def test_brain_004_can_set_get_false(self):
		self.brain.set_value('test', False)
		self.assertFalse(self.brain.get_value('test'))

	def test_brain_005_can_set_get_none(self):
		self.brain.set_value('test')
		self.assertIsNone(self.brain.get_value('test'))
		self.assertFalse(self.brain.get_value('test'))


	def test_brain_101_can_count_tweets_empty(self):
		self.assertEqual(0, self.brain.count_tweets())

	def test_brain_102_can_add_has_tweet(self):
		tweet = mock.Mock(id = 111, user = self.user1)
		self.assertFalse(self.brain.has_tweet(tweet))
		self.assertEqual(1, self.brain.add_tweet(tweet, 'test'))
		self.assertTrue(self.brain.has_tweet(tweet))

	def test_brain_103_not_updating_tweets(self):
		tweet = mock.Mock(id = 111, user = self.user1)
		self.assertFalse(self.brain.has_tweet(tweet))
		self.assertEqual(1, self.brain.add_tweet(tweet, 'test'))
		self.assertEqual(0, self.brain.add_tweet(tweet, 'test'))

	def test_brain_104_can_count_tweets(self):
		self.brain.add_tweet(mock.Mock(id = 111, user = self.user1), 'test')
		self.brain.add_tweet(mock.Mock(id = 222, user = self.user1), 'test')
		self.assertEqual(2, self.brain.count_tweets())
		self.brain.add_tweet(mock.Mock(id = 333, user = self.user2), 'test')
		self.assertEqual(3, self.brain.count_tweets())

	def test_brain_105_can_count_tweets_by_reason(self):
		self.brain.add_tweet(mock.Mock(id = 111, user = self.user1), 'A')
		self.brain.add_tweet(mock.Mock(id = 222, user = self.user1), 'B')
		self.brain.add_tweet(mock.Mock(id = 333, user = self.user2), 'A')
		self.assertEqual(2, self.brain.count_tweets(reason = 'A'))
		self.assertEqual(1, self.brain.count_tweets(reason = 'B'))
		self.assertEqual(0, self.brain.count_tweets(reason = '?'))

	def test_brain_106_can_count_tweets_by_screen_name(self):
		self.brain.add_tweet(mock.Mock(id = 111, user = self.user1), 'A')
		self.brain.add_tweet(mock.Mock(id = 222, user = self.user1), 'B')
		self.brain.add_tweet(mock.Mock(id = 333, user = self.user2), 'A')
		self.assertEqual(2, self.brain.count_tweets(user_screen_name = self.user1.screen_name))
		self.assertEqual(1, self.brain.count_tweets(user_screen_name = self.user2.screen_name))
		self.assertEqual(0, self.brain.count_tweets(user_screen_name = '?'))

	def test_brain_107_can_count_tweets_by_reson_and_screen_name(self):
		self.brain.add_tweet(mock.Mock(id = 111, user = self.user1), 'A')
		self.brain.add_tweet(mock.Mock(id = 222, user = self.user1), 'B')
		self.brain.add_tweet(mock.Mock(id = 333, user = self.user2), 'A')
		self.assertEqual(1, self.brain.count_tweets(reason = 'A', user_screen_name = self.user1.screen_name))
		self.assertEqual(1, self.brain.count_tweets(reason = 'B', user_screen_name = self.user1.screen_name))
		self.assertEqual(1, self.brain.count_tweets(reason = 'A', user_screen_name = self.user2.screen_name))
		self.assertEqual(0, self.brain.count_tweets(reason = '?', user_screen_name = '?'))


	def __data_for_test_201(self):
		for user in [ self.user1, self.user2, self.user3 ]:
			yield user

	def test_brain_201_can_add_has_user(self):
		for table in ['followers', 'friends']:
			self.assertFalse(self.brain.has_user(table, self.user3.id))
			self.assertEqual(1, self.brain.add_user(table, self.user3))
			self.assertTrue(self.brain.has_user(table, self.user3.id))

	def test_brain_201_can_handle_users_stream(self):
		for table in ['followers', 'friends']:
			self.brain.import_users(table , self.__data_for_test_201)
			self.assertEqual(3, len(self.brain.users(table)))

	def test_brain_201_can_handle_users_array(self):
		for table in ['followers', 'friends']:
			data = self.__data_for_test_201()
			self.brain.import_users(table , data)
			self.assertEqual(3, len(self.brain.users(table)))


	def test_brain_301_metrics_complete(self):
		metrics = self.brain.metrics()
		self.assertTrue('0' in metrics)
		self.assertTrue('(' in metrics)
		self.assertTrue(')' in metrics)
		self.assertTrue('tweets' in metrics)
		self.assertTrue('followers' in metrics)
		self.assertTrue('friends' in metrics)
		self.assertTrue('config values' in metrics)



##
##
class CommandLineTest(TestCase):

	@contextmanager
	def captured_output(self):
	    old_out, old_err = sys.stdout, sys.stderr
	    try:
	        sys.stdout, sys.stderr = StringIO(), StringIO()
	        yield sys.stdout, sys.stderr
	    finally:
	        sys.stdout, sys.stderr = old_out, old_err

	def setUp(self):
		pass


	def test_000_run_show_help(self):
		sys.argv = []
		with self.captured_output() as (out, err):
			self.assertEqual(0, karlsruher.CommandLine.run())
		self.assertEqual('@Karlsruher', out.getvalue().strip()[:11])

	def test_001_run_show_help(self):
		sys.argv = ['-help']
		with self.captured_output() as (out, err):
			self.assertEqual(0, karlsruher.CommandLine.run())
		self.assertEqual('@Karlsruher', out.getvalue().strip()[:11])


	def test_101_run_housekeeping_no_home(self):
		sys.argv = ['-housekeeping']
		with self.captured_output() as (out, err):
			self.assertEqual(1, karlsruher.CommandLine.run())
		self.assertEqual('No home directory', out.getvalue().strip()[:17])

	def test_102_run_read_no_home(self):
		sys.argv = ['-read']
		with self.captured_output() as (out, err):
			self.assertEqual(1, karlsruher.CommandLine.run())
		self.assertEqual('No home directory', out.getvalue().strip()[:17])

	def test_103_run_talk_no_home(self):
		sys.argv = ['-talk']
		with self.captured_output() as (out, err):
			self.assertEqual(1, karlsruher.CommandLine.run())
		self.assertEqual('No home directory', out.getvalue().strip()[:17])


	def test_201_run_housekeeping_nonexisting_home(self):
		sys.argv = ['-housekeeping', '--home=/does/not/exist']
		with self.captured_output() as (out, err):
			self.assertEqual(1, karlsruher.CommandLine.run())
		self.assertEqual('Specified home', out.getvalue().strip()[:14])

	def test_202_run_read_nonexisting_home(self):
		sys.argv = ['-read', '--home=/does/not/exist']
		with self.captured_output() as (out, err):
			self.assertEqual(1, karlsruher.CommandLine.run())
		self.assertEqual('Specified home', out.getvalue().strip()[:14])

	def test_203_run_talk_nonexisting_home(self):
		sys.argv = ['-talk', '--home=/does/not/exist']
		with self.captured_output() as (out, err):
			self.assertEqual(1, karlsruher.CommandLine.run())
		self.assertEqual('Specified home', out.getvalue().strip()[:14])


	def test_301_run_housekeeping_with_home(self):
		sys.argv = ['-housekeeping', '--home=' + tempfile.gettempdir()]
		with self.captured_output() as (out, err):
			self.assertEqual(1, karlsruher.CommandLine.run())
		self.assertEqual('Missing credentials', out.getvalue().strip()[:19])

	def test_302_run_read_with_home(self):
		sys.argv = ['-read', '--home=' + tempfile.gettempdir()]
		with self.captured_output() as (out, err):
			self.assertEqual(1, karlsruher.CommandLine.run())
		self.assertEqual('Missing credentials', out.getvalue().strip()[:19])

	def test_303_run_with_talk(self):
		sys.argv = ['-talk', '--home=' + tempfile.gettempdir()]
		with self.captured_output() as (out, err):
			self.assertEqual(1, karlsruher.CommandLine.run())
		self.assertEqual('Missing credentials', out.getvalue().strip()[:19])


	@mock.patch.object(karlsruher.Karlsruher, '__init__', lambda x,y:None)
	@mock.patch.object(karlsruher.Karlsruher, 'lock', mock.Mock())
	@mock.patch.object(karlsruher.Karlsruher, 'logger', mock.Mock())
	@mock.patch.object(
		karlsruher.Karlsruher, 'twitter',
		mock.MagicMock(
			connect = mock.Mock(),
			me = mock.Mock(screen_name='testbot')
		)
	)
	def test_400_run_with_talk_mock_(self):
		sys.argv = ['-talk', '--home=' + tempfile.gettempdir()]
		self.assertEqual(0, karlsruher.CommandLine.run())
