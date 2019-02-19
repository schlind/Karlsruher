## Karlsruher Retweet Bot
## https://github.com/schlind/Karlsruher

from sys import version_info as python_version
assert python_version >= (3,)

##
##
from datetime import datetime
import logging
import sqlite3
import tempfile
import tweepy
from os import path, remove
from sys import argv
from unittest import mock, TestCase
from unittest import TestLoader, TestResult, TestSuite, TextTestRunner

##
##
class Karlsruher:

	def __init__(self, home, twitter = None, database = None):

		if not path.isdir(home):
			raise Exception('Please specify a valid "home" directory.')

		self.logger = logging.getLogger(self.__class__.__name__)

		self.twitter = twitter if twitter else Twitter(home + '/credentials.py')
		self.me = self.twitter.me()
		self.logger.info('Hello, my name is @%s.', self.me.screen_name)

		name = self.me.screen_name.lower()
		self.lock = Lock(home + '/.lock.' + name)

		self.brain = Brain(database if database else home + '/'+ name + '.db')
		self.logger.info('Having %s in brain.', self.brain.metrics())

		self.advisors = []
		for user in self.twitter.list_advisors():
			self.advisors.append(str(user.id))
		self.logger.debug('Having %s advisors.', len(self.advisors))

		self.doReply = False
		self.doRetweet = False


	def houseKeeping(self):

		if not self.lock.acquire():
			self.logger.debug('Housekeeping locked by "%s".', self.lock.path)
			return False

		self.logger.info('Housekeeping! This may take a while...')

		watch = StopWatch()
		try:
			self.brain.importUsers('followers', self.twitter.followers)
			self.brain.importUsers('friends', self.twitter.friends)
		except:
			self.logger.exception('Exception during housekeeping!')
		self.logger.info('Housekeeping done, took %s.', watch.elapsedTime())
		self.lock.release()
		return True


	def readMentions(self):

		if not self.lock.acquire():
			self.logger.debug('Reading locked by "%s".', self.lock.path)
			return False

		self.logger.info('Reading mentions...')

		watch = StopWatch()
		for mention in self.twitter.mentions_timeline():
			try:
				self.readMention(mention)
			except:
				self.logger.exception('Exception while reading mention.')

		self.logger.info('Reading done, took %s.', watch.elapsedTime())
		self.lock.release()
		return True


	def readMention(self, tweet):

		tweetLog = '@{}/{}'.format(tweet.user.screen_name, tweet.id)

		if self.brain.hasTweet(tweet):
			self.logger.info('%s read before.', tweetLog)
			return False

		appliedAction = 'readMention'

		for action in [ self.adviceAction, self.retweetAction ]:
			if action(tweet):
				appliedAction = action.__name__
				break

		self.brain.addTweet(tweet, appliedAction)
		self.logger.info('%s applied %s.', tweetLog, appliedAction)
		return True


	def adviceAction(self, tweet):

		if not str(tweet.user.id) in self.advisors:
			self.logger.debug('@%s is not an advisor.', tweet.user.screen_name)
			return False ## not an advisor

		message = str(tweet.text)
		trigger = '@{}!'.format(self.me.screen_name.lower())
		if not message.lower().startswith(trigger):
			self.logger.debug('@%s gave no advice.', tweet.user.screen_name)
			return False ## not an advice

		advice = message[len(trigger):].strip()

		if advice.lower().startswith('geh schlafen!'):
			self.logger.info(
				'Taking advice from @%s: %s', tweet.user.screen_name, advice
			)
			self.brain.setValue('retweet.disabled', True)
			self.reply(tweet, 'Ok @{}, ich retweete nicht mehr... (Automatische Antwort)')
			return True ## took advice

		if advice.lower().startswith('wach auf!'):
			self.logger.info(
				'Taking advice from @%s: %s', tweet.user.screen_name, advice
			)
			self.brain.setValue('retweet.disabled', None)
			self.reply(tweet, 'Ok @{}, ich retweete wieder... (Automatische Antwort)')
			return True ## took advice

		return False ## did not take advice


	def reply(self, tweet, status):

		status = status.format(tweet.user.screen_name)
		self.logger.debug(
			'%s: "%s"', 'Reply' if self.doReply else 'Would reply', status
		)
		if self.doReply:
			self.twitter.update_status(
				in_reply_to_status_id = tweet.id,
				status = status.format(tweet.user.screen_name)
			)


	def retweetAction(self, tweet):

		if self.brain.getValue('retweet.disabled') == True:
			self.logger.debug('I am sleeping and not retweeting.')
			return False ## no retweets

		if str(tweet.user.screen_name) == str(self.me.screen_name):
			self.logger.debug('@%s is me, no retweet.', tweet.user.screen_name)
			return False ## not retweeting myself

		if str(tweet.user.protected) == 'True':
			self.logger.debug('@%s protected, no retweet.', tweet.user.screen_name)
			return False ## can't retweet protected users

		if str(tweet.in_reply_to_status_id) != 'None':
			self.logger.debug('@%s reply, no retweet.', tweet.user.screen_name)
			return False ## not retweeting replies

		if not self.brain.hasUser('followers', tweet.user.id):
			self.logger.debug('@%s not following, no retweet.', tweet.user.screen_name)
			return False ## not retweeting non-followers

		self.logger.debug('%s: @%s/%s.',
			'Retweet' if self.doRetweet else 'Would retweet',
			tweet.user.screen_name, tweet.id
		)

		if self.doRetweet:
			self.twitter.retweet(tweet)

		return True ## logically retweeted


##
##
class KarlsruherTest(TestCase):

	def setUp(self):
		self.me = mock.Mock(id = 12345678900, screen_name = 'MockBot')
		self.advisor = mock.Mock(id = 750000, screen_name = 'advisor')
		self.follower = mock.Mock(id = 54321, screen_name = 'follower')
		self.friend = mock.Mock(id = 1111111, screen_name = 'friend')
		self.unknown = mock.Mock(id = 700007, screen_name = 'unknown')
		self.tweet = mock.Mock(
			in_reply_to_status_id = None,
			id = 721721721,
			user = self.unknown,
			text = 'Test @' + self.me.screen_name + ' mention.'
		)
		self.bot = Karlsruher(
			home = tempfile.gettempdir(),
			database = ':memory:',
			twitter = mock.Mock(
				me = mock.MagicMock(return_value = self.me),
				list_advisors = mock.MagicMock(return_value = [self.advisor]),
				followers = mock.MagicMock(return_value = [self.follower,self.advisor]),
				friends = mock.MagicMock(return_value = [self.friend]),
				update_status = mock.Mock(),
				retweet = mock.Mock()
			)
		)

	def tearDown(self):
		self.bot.lock.release()

	def test_001_not_locked(self):
		self.assertFalse(self.bot.lock.isPresent())

	def test_101_init_can_get_me(self):
		self.assertEqual(self.bot.me.screen_name, self.me.screen_name)
		self.assertEqual(1, self.bot.twitter.me.call_count)

	def test_102_init_can_load_advisors(self):
		self.assertEqual(1, self.bot.twitter.list_advisors.call_count)
		self.assertEqual(1, len(self.bot.advisors))
		self.assertTrue(str(self.advisor.id) in self.bot.advisors)
		self.assertFalse(str(self.unknown.id) in self.bot.advisors)


	def test_201_empty_brain(self):
		self.assertEqual(0, self.bot.brain.countTweets())
		self.assertEqual(0, len(self.bot.brain.users('followers')))
		self.assertEqual(0, len(self.bot.brain.users('friends')))
		self.assertIsNone(self.bot.brain.getValue('retweet.disabled'))


	def test_302_housekeeping(self):
		self.bot.houseKeeping()
		self.assertEqual(2, len(self.bot.brain.users('followers')))
		self.assertEqual(1, len(self.bot.brain.users('friends')))


	def test_401_mention_can_read(self):
		self.assertTrue(self.bot.readMention(self.tweet))

	def test_402_mention_can_read_only_once(self):
		self.assertTrue(self.bot.readMention(self.tweet))
		self.assertFalse(self.bot.readMention(self.tweet))


	def test_501_advice_can_ignore_from_non_advisors(self):
		self.tweet.text = '@{}! gEh scHlafen!!!'.format(self.me.screen_name)
		self.assertFalse(self.bot.adviceAction(self.tweet))

	def test_502_advice_can_accept_sleep(self):
		self.tweet.text = '@{}! gEh scHlafen!!!'.format(self.me.screen_name)
		self.tweet.user = self.advisor
		self.assertTrue(self.bot.adviceAction(self.tweet))
		self.assertTrue(self.bot.brain.getValue('retweet.disabled'))

	def test_503_advice_can_accept_wakeup(self):
		self.tweet.text = '@{}! waCh auf!!!'.format(self.me.screen_name)
		self.tweet.user = self.advisor
		self.bot.brain.setValue('retweet.disabled', True)
		self.assertTrue(self.bot.adviceAction(self.tweet))
		self.assertIsNone(self.bot.brain.getValue('retweet.disabled'))


	def test_601_retweet_not_during_sleep(self):
		self.bot.houseKeeping()
		self.bot.doRetweet = True
		self.tweet.user = self.follower
		self.bot.brain.setValue('retweet.disabled', True)
		self.assertFalse(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_602_retweet_not_myself(self):
		self.bot.houseKeeping()
		self.bot.doRetweet = True
		self.tweet.user = self.me
		self.assertFalse(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_603_retweet_not_protected(self):
		self.bot.houseKeeping()
		self.bot.doRetweet = True
		for user in [
			self.me, self.advisor, self.follower, self.friend, self.unknown
		]:
			self.tweet.user = user
			self.tweet.user.protected = True
			self.assertFalse(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_604_retweet_not_replies(self):
		self.bot.houseKeeping()
		self.bot.doRetweet = True
		self.tweet.in_reply_to_status_id = 7500
		for user in [
			self.me, self.advisor, self.follower, self.friend, self.unknown
		]:
			self.tweet.user = user
			self.assertFalse(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_604_retweet_not_non_followers(self):
		self.bot.houseKeeping()
		self.bot.doRetweet = True
		self.assertFalse(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_605_retweet_follower(self):
		self.bot.houseKeeping()
		self.bot.doRetweet = True
		self.tweet.user = self.follower
		self.assertTrue(self.bot.retweetAction(self.tweet))
		self.assertEqual(1, self.bot.twitter.retweet.call_count)

	def test_606_retweet_not_when_disabled(self):
		self.bot.houseKeeping()
		self.bot.doRetweet = False
		for user in [self.follower, self.advisor ]:
			self.tweet.user = user
			self.assertTrue(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)


##
##
class Brain:

	schema = [
		'CREATE TABLE IF NOT EXISTS config (name VARCHAR PRIMARY KEY, value VARCHAR DEFAULT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)',
		'CREATE TABLE IF NOT EXISTS tweets (id VARCHAR PRIMARY KEY, user_screen_name VARCHAR NOT NULL, reason VARCHAR NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)',
		'CREATE TABLE IF NOT EXISTS followers (id VARCHAR PRIMARY KEY, screen_name VARCHAR NOT NULL, state INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)',
		'CREATE TABLE IF NOT EXISTS friends (id VARCHAR PRIMARY KEY, screen_name VARCHAR NOT NULL, state INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)',
	]

	def __init__(self, database):

		self.logger = logging.getLogger(self.__class__.__name__)

		self.db = sqlite3.connect(database)
		self.db.row_factory = sqlite3.Row

		for createTable in self.schema:
			self.db.cursor().execute(createTable)
			self.db.commit()


	def setValue(self, name, value = None):

		cursor = self.db.cursor()
		if value == None:
			self.logger.debug('Unsetting value "%s"', name)
			cursor.execute('DELETE FROM config WHERE name = ?', (str(name),))
		else:
			self.logger.debug('Setting value "%s"', name)
			cursor.execute(
				'INSERT OR REPLACE INTO config (name,value) VALUES (?,?)',
				(str(name), str(value))
			)
		self.db.commit()
		return cursor.rowcount


	def getValue(self, name, default = None):

		self.logger.debug('Getting value "%s"', name)

		cursor = self.db.cursor()
		cursor.execute('SELECT value FROM config WHERE name = ?', (str(name),))
		value = cursor.fetchone()

		if value:
			value = value['value']
			if value == 'True':
				value = True
			elif value == 'False':
				value = False
			elif value == 'None':
				value = None
			return value

		return default


	def hasTweet(self, tweet):

		cursor = self.db.cursor()
		cursor.execute('SELECT id FROM tweets WHERE id = ?', (str(tweet.id),))
		haveTweet = cursor.fetchone() != None
		self.logger.debug('%s tweet "%s".',
			'Having' if haveTweet else 'Not having',
			tweet.id
		)
		return haveTweet


	def addTweet(self, tweet, reason):

		self.logger.debug('Adding tweet "%s".', tweet.id)

		cursor = self.db.cursor()
		cursor.execute(
			'INSERT OR IGNORE INTO tweets (id,user_screen_name,reason) VALUES (?,?,?)',
			(str(tweet.id), str(tweet.user.screen_name), str(reason))
		)
		self.db.commit()
		return cursor.rowcount


	def countTweets(self, screenName = None, reason = None):

		count = 'SELECT COUNT(id) AS count FROM tweets'
		where = ()
		if screenName and reason:
			count += ' WHERE user_screen_name = ? AND reason = ?'
			where = (str(screenName), str(reason))
		elif screenName:
			count += ' WHERE user_screen_name = ?'
			where = (str(screenName),)
		elif reason:
			count += ' WHERE reason = ?'
			where = (str(reason),)

		cursor = self.db.cursor()
		cursor.execute(count, where)
		countValue = cursor.fetchone()['count']

		self.logger.debug('Count tweets%s%s: %s.',
			' by @' + screenName if screenName else '',
			', reason=' + reason if reason else '',
			countValue
		)

		return countValue


	def users(self, table):

		cursor = self.db.cursor()
		cursor.execute(
			'SELECT id FROM {} WHERE state > 0'.format(table)
		)
		users = cursor.fetchall()
		self.logger.debug('Fetched %s users from table "%s".', len(users), table)
		return users


	def hasUser(self, table, userId):

		cursor = self.db.cursor()
		cursor.execute(
			'SELECT id, screen_name FROM {} WHERE state > 0 AND id = ?'.format(table),
			(str(userId),)
		)
		hasUser = cursor.fetchone() != None
		self.logger.debug(
			'%s user "%s" in "%s".',
			'Having' if hasUser else 'Not having', userId, table
		)
		return hasUser


	def importUsers(self, table, source):

		limbo = self.db.cursor()
		limbo.execute('UPDATE {} SET state = 2 WHERE state = 1'.format(table))
		self.db.commit()

		if callable(source):
			for user in source():
				self.addUser(table, user, 3)
		else:
			for user in source:
				self.addUser(table, user, 3)

		nirvana = self.db.cursor()
		nirvana.execute('UPDATE {} SET state = 0 WHERE state = 2'.format(table))
		self.db.commit()

		imported = self.db.cursor()
		imported.execute('UPDATE {} SET state = 1 WHERE state = 3'.format(table))
		self.db.commit()

		self.logger.info(
			'Updated %s %s, %s imported, %s lost.',
			limbo.rowcount, table, imported.rowcount, nirvana.rowcount
		)


	def addUser(self, table, user, state = 1):

		self.logger.debug(
			'Adding user "%s" to "%s"', user.screen_name, table
		)
		cursor = self.db.cursor()
		cursor.execute(
			'INSERT OR REPLACE INTO {} (id,screen_name,state) VALUES (?,?,?)'.format(table),
			(str(user.id), str(user.screen_name), state)
		)
		self.db.commit()
		return cursor.rowcount


	def metrics(self):

		cursor = self.db.cursor()

		cursor.execute('SELECT COUNT(id) AS count FROM tweets')
		tweetCount = cursor.fetchone()['count']

		cursor.execute('SELECT COUNT(id) AS count FROM followers WHERE state > 0')
		followerCount = cursor.fetchone()['count']

		cursor.execute('SELECT COUNT(id) AS count FROM followers WHERE state = 0')
		orphanFollowerCount = cursor.fetchone()['count']

		cursor.execute('SELECT COUNT(id) AS count FROM friends WHERE state > 0')
		friendCount = cursor.fetchone()['count']

		cursor.execute('SELECT COUNT(id) AS count FROM friends WHERE state = 0')
		orphanFriendCount = cursor.fetchone()['count']

		cursor.execute('SELECT COUNT(name) AS count FROM config')
		configCount = cursor.fetchone()['count']

		return '{} tweets, {}({}) followers, {}({}) friends, {} config values'.format(
			tweetCount, followerCount, orphanFollowerCount,
			friendCount, orphanFriendCount, configCount
		)


##
##
class BrainTest(TestCase):

	def setUp(self):
		self.user1 = mock.Mock(id = 1, screen_name = 'user1')
		self.user2 = mock.Mock(id = 2, screen_name = 'user2')
		self.user3 = mock.Mock(id = 3, screen_name = 'user3')
		self.brain = Brain(':memory:')

	def test_brain_001_can_get_default_value(self):
		self.assertEqual('default', self.brain.getValue('test', 'default'))

	def test_brain_002_can_set_get_string_value(self):
		self.brain.setValue('test', 'string')
		self.assertEqual('string', self.brain.getValue('test'))

	def test_brain_003_can_set_get_true(self):
		self.brain.setValue('test', True)
		self.assertTrue(self.brain.getValue('test'))

	def test_brain_004_can_set_get_false(self):
		self.brain.setValue('test', False)
		self.assertFalse(self.brain.getValue('test'))

	def test_brain_005_can_set_get_none(self):
		self.brain.setValue('test')
		self.assertIsNone(self.brain.getValue('test'))
		self.assertFalse(self.brain.getValue('test'))


	def test_brain_101_can_count_tweets_empty(self):
		self.assertEqual(0, self.brain.countTweets())

	def test_brain_102_can_add_has_tweet(self):
		tweet = mock.Mock(id = 111, user = self.user1)
		self.assertFalse(self.brain.hasTweet(tweet))
		self.assertEqual(1, self.brain.addTweet(tweet, 'test'))
		self.assertTrue(self.brain.hasTweet(tweet))

	def test_brain_103_not_updating_tweets(self):
		tweet = mock.Mock(id = 111, user = self.user1)
		self.assertFalse(self.brain.hasTweet(tweet))
		self.assertEqual(1, self.brain.addTweet(tweet, 'test'))
		self.assertEqual(0, self.brain.addTweet(tweet, 'test'))

	def test_brain_104_can_count_tweets(self):
		self.brain.addTweet(mock.Mock(id = 111, user = self.user1), 'test')
		self.brain.addTweet(mock.Mock(id = 222, user = self.user1), 'test')
		self.assertEqual(2, self.brain.countTweets())
		self.brain.addTweet(mock.Mock(id = 333, user = self.user2), 'test')
		self.assertEqual(3, self.brain.countTweets())

	def test_brain_105_can_count_tweets_by_reason(self):
		self.brain.addTweet(mock.Mock(id = 111, user = self.user1), 'A')
		self.brain.addTweet(mock.Mock(id = 222, user = self.user1), 'B')
		self.brain.addTweet(mock.Mock(id = 333, user = self.user2), 'A')
		self.assertEqual(2, self.brain.countTweets(reason = 'A'))
		self.assertEqual(1, self.brain.countTweets(reason = 'B'))
		self.assertEqual(0, self.brain.countTweets(reason = '?'))

	def test_brain_106_can_count_tweets_by_screen_name(self):
		self.brain.addTweet(mock.Mock(id = 111, user = self.user1), 'A')
		self.brain.addTweet(mock.Mock(id = 222, user = self.user1), 'B')
		self.brain.addTweet(mock.Mock(id = 333, user = self.user2), 'A')
		self.assertEqual(2, self.brain.countTweets(screenName = self.user1.screen_name))
		self.assertEqual(1, self.brain.countTweets(screenName = self.user2.screen_name))
		self.assertEqual(0, self.brain.countTweets(screenName = '?'))

	def test_brain_107_can_count_tweets_by_reson_and_screen_name(self):
		self.brain.addTweet(mock.Mock(id = 111, user = self.user1), 'A')
		self.brain.addTweet(mock.Mock(id = 222, user = self.user1), 'B')
		self.brain.addTweet(mock.Mock(id = 333, user = self.user2), 'A')
		self.assertEqual(1, self.brain.countTweets(reason = 'A', screenName = self.user1.screen_name))
		self.assertEqual(1, self.brain.countTweets(reason = 'B', screenName = self.user1.screen_name))
		self.assertEqual(1, self.brain.countTweets(reason = 'A', screenName = self.user2.screen_name))
		self.assertEqual(0, self.brain.countTweets(reason = '?', screenName = '?'))


	def __data_for_test_201(self):
		for user in [ self.user1, self.user2, self.user3 ]:
			yield user

	def test_brain_201_can_add_has_user(self):
		for table in ['followers', 'friends']:
			self.assertFalse(self.brain.hasUser(table, self.user3.id))
			self.assertEqual(1, self.brain.addUser(table, self.user3))
			self.assertTrue(self.brain.hasUser(table, self.user3.id))

	def test_brain_201_can_handle_users_stream(self):
		for table in ['followers', 'friends']:
			self.brain.importUsers(table , self.__data_for_test_201)
			self.assertEqual(3, len(self.brain.users(table)))

	def test_brain_201_can_handle_users_array(self):
		for table in ['followers', 'friends']:
			data = self.__data_for_test_201()
			self.brain.importUsers(table , data)
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
class Twitter:

	def __init__(self, credentials):

		if not path.isfile(credentials):
			raise Exception('''Missing credentials file!

Please create file "{}" with contents:

TWITTER_CONSUMER_KEY = 'Your Consumer Key'
TWITTER_CONSUMER_SECRET = 'Your Consumer Secret'
TWITTER_ACCESS_KEY = 'Your Access Key'
TWITTER_ACCESS_SECRET = 'Your Access Secret'

'''.format(credentials)
			)

		from credentials import \
			TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, \
			TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET

		oauth = tweepy.OAuthHandler(
			TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
		)
		oauth.set_access_token(TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET)

		self.api = tweepy.API(
			oauth, compression = True,
			wait_on_rate_limit = True, wait_on_rate_limit_notify = True
		)


	def me(self):
		return self.api.me()

	def mentions_timeline(self):
		return self.api.mentions_timeline()

	def list_advisors(self):
		self.api.list_members.pagination_mode = 'cursor'
		for advisor in tweepy.Cursor(
			self.api.list_members, self.me().screen_name, 'advisors'
		).items():
			yield advisor

	def followers(self):
		self.api.followers.pagination_mode = 'cursor'
		for follower in tweepy.Cursor(self.api.followers).items():
			yield follower

	def friends(self):
		self.api.friends.pagination_mode = 'cursor'
		for friend in tweepy.Cursor(self.api.friends).items():
			yield friend

	def retweet(self, tweet):
		return self.api.retweet(tweet.id)

	def update_status(self, status, in_reply_to_status_id = None):
		if in_reply_to_status_id:
			return self.api.update_status(
				in_reply_to_status_id = in_reply_to_status_id, status = status
			)
		return self.api.update_status(status = status)


##
##
class StopWatch:

	def __init__(self):
		self.start = datetime.now()

	def elapsedTime(self):
		return datetime.now() - self.start


##
##
class StopWatchTest(TestCase):

	def test_watch_001_can_read_elapsed_time(self):
		self.assertEqual('0:00:00.00' , str(StopWatch().elapsedTime())[:10])


##
##
class Lock:

	def __init__(self, path):
		self.path = path

	def isPresent(self):
		return path.isfile(self.path)

	def acquire(self):
		if self.isPresent():
			return False
		open(self.path, 'a').close()
		return self.isPresent()

	def release(self):
		if self.isPresent():
			remove(self.path)


##
##
class LockTest(TestCase):

	def setUp(self):
		self.lock = Lock(tempfile.gettempdir() + '/LockTest.tmp')

	def tearDown(self):
		self.lock.release()

	def test_lock_001_can_indicate(self):
		self.assertFalse(self.lock.isPresent())

	def test_lock_002_can_acquire_and_indicate(self):
		self.assertTrue(self.lock.acquire())
		self.assertTrue(self.lock.isPresent())

	def test_lock_003_can_acquire_only_once(self):
		self.assertTrue(self.lock.acquire())
		self.assertFalse(self.lock.acquire())

	def test_lock_004_can_release(self):
		self.lock.release()
		self.assertFalse(self.lock.isPresent())


##
##
class SelfTest:

	testCases = [ StopWatchTest, LockTest, BrainTest, KarlsruherTest ]

	@staticmethod
	def getSuite():
		suite = TestSuite()
		loader = TestLoader()
		for testCase in SelfTest.testCases:
			suite.addTest(loader.loadTestsFromTestCase(testCase))
		return suite

	@staticmethod
	def runVerbose():
		TextTestRunner(
			verbosity = 2, failfast = True
		).run(SelfTest.getSuite())

	@staticmethod
	def isSuccessful():
		result = TestResult()
		result.failfast = True
		SelfTest.getSuite().run(result)
		return 0 == len(result.errors) == len(result.failures)


##
##
class CommandLine:

	"""@Karlsruher Retweet Robot command line

  Run Modes:

	-test	Only perform self-tests verbosely and exit.

  or:

	-read	Read timelines and trigger activities.

    and add activities:

		-retweet	Send retweets.
		-reply		Send replies.

  or:

	-talk	Combines "-read" and all activities.

	# Cronjob (every 5 minutes):
	*/5 * * * * /path/to/karlsruher/run.py -talk >/dev/null 2>&1


  or:

	-housekeeping	Perform housekeeping tasks and exit.
		This fetches followers and friends from Twitter.
		Due to API Rate Limits, housekeeping is throttled
		and takes up to 1 hour per 1000 followers/friends.
		Run this nightly once per day.

	# Cronjob (once per day):
	3 3 * * * /path/to/karlsruher/run.py -housekeeping >/dev/null 2>&1


  or:

	-help	You are reading this right now.


  Add "-debug" to raise overall logging level.
	"""


	@staticmethod
	def run(home):

		if '-test' in argv:
			logging.basicConfig(
				level = logging.DEBUG if '-debug' in argv else logging.ERROR,
				format = '%(levelname)-5.5s [%(name)s.%(funcName)s]: %(message)s',
				handlers = [logging.StreamHandler()]
			)
			SelfTest.runVerbose()
			exit(0)

		if not SelfTest.isSuccessful():
			SelfTest.runVerbose()
			print("Selftest failed, aborting.")
			exit(1)

		logging.basicConfig(
			level = logging.DEBUG if '-debug' in argv else logging.INFO,
			format = '%(asctime)s %(levelname)-5.5s [%(name)s.%(funcName)s]: %(message)s',
			handlers = [logging.StreamHandler()]
		)

		if '-housekeeping' in argv:
			Karlsruher(home).houseKeeping()
			exit(0)

		if '-read' in argv or '-talk' in argv:
			karlsruher = Karlsruher(home)
			karlsruher.doReply = '-reply' in argv or '-talk' in argv
			karlsruher.doRetweet = '-retweet' in argv or '-talk' in argv
			karlsruher.readMentions()
			exit(0)

		print(CommandLine.__doc__)
		exit(0)


##
## Fin
