#!/usr/bin/env python3
## Karlsruher Retweet Bot https://github.com/schlind/Karlsruher
from sys import version_info as python_version
assert python_version >= (3,)

import logging
import sqlite3
import tweepy

from datetime import datetime
from os import path as fs, remove


class Karlsruher:

	logger = None
	twitter = None

	## sqlite3 connection
	db = None

	## a file to lock active instances against each other
	lockFile = None

	## a file to disable the retweet feature on-the-fly
	sleepFile = None

	## the Twitter user of the bot
	me = None

	## the list slug for the list of advisors on Twitter
	advisorListSlug = 'advisors'
	advisors = []
	followers = []
	friends = []

	## features
	doRetweets = False
	doReplying = False
	doTweeting = False


	def __init__(self, workDir, twitterClient = None, database = None):
		"""
		Initialize connections to and load required data
		from Twitter and database.

		workDir - a directory for persistence
		twitter - optional, a mock for tests
		database - optional, for tests
		"""
		if not workDir:
			raise Exception('No workDir specified.')

		self.logger = logging.getLogger(__name__)

		## take a specified client or create a new instance.
		self.twitter = twitterClient if twitterClient else TwitterClient(workDir)
		self.me = self.twitter.me()

		self.logger.info('Hello, my name is @%s.', self.me.screen_name)

		self.lockFile = workDir + '/.lock.' + self.me.screen_name.lower()
		self.sleepFile = workDir + '/.sleep.' + self.me.screen_name.lower()

		self.initDatabase(
			## take a specified database or use a default file.
			database if database else workDir + '/'+ self.me.screen_name.lower() + '.db'
		)

		self.initAdvisors(self.advisorListSlug)
		self.initFollowers()
		self.initFriends()




	def acquireLock(self, lockFile = None):
		"""Try to create a lockfile and return True when a new lockfile was
		created, otherwise False."""
		if not lockFile:
			lockFile = self.lockFile
		if fs.isfile(lockFile):
			self.logger.debug('Is already locked: %s', lockFile)
			return False
		self.logger.debug('Locking: %s', lockFile)
		open(lockFile, 'a').close()
		return True

	def returnLock(self, lockFile = None):
		"""Remove a lockfile."""
		if not lockFile:
			lockFile = self.lockFile
		self.logger.debug('Unlocking: %s', lockFile)
		if fs.isfile(lockFile):
			remove(lockFile)

	def isLocked(self, lockFile = None):
		"""Return True when a lockfile exists, otherwise False."""
		if not lockFile:
			lockFile = self.lockFile
		if fs.isfile(lockFile):
			self.logger.debug('Is locked: %s', lockFile)
			return True
		return False




	def initDatabase(self, database):
		"""Connect to database and ensure tables exist."""

		createTables = [
			'CREATE TABLE IF NOT EXISTS tweets (id VARCHAR PRIMARY KEY, user_screen_name VARCHAR NOT NULL, reason VARCHAR NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)',
			'CREATE TABLE IF NOT EXISTS followers (id VARCHAR PRIMARY KEY, screen_name VARCHAR NOT NULL, state INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)',
			'CREATE TABLE IF NOT EXISTS friends (id VARCHAR PRIMARY KEY, screen_name VARCHAR NOT NULL, state INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)'
		]

		self.logger.debug('Using "%s" as database.', database)
		self.db = sqlite3.connect(database)
		self.db.row_factory = sqlite3.Row
		for createTable in createTables:
			self.db.cursor().execute(createTable)
			self.db.commit()

	def rememberTweet(self, tweetId, userScreenName, reason = 'non reason given'):
		"""Store a tweet's id, user's screen_name and a reason to database."""

		self.logger.debug('Remembering tweet %s', tweetId)
		remember = self.db.cursor()
		remember.execute(
			'INSERT OR IGNORE INTO tweets (id,user_screen_name,reason) VALUES (?,?,?)', (str(tweetId),str(userScreenName),str(reason))
		)
		self.db.commit()
		return remember.rowcount

	def haveReadTweet(self, tweetId):
		"""Indicate whether a tweet was read before or not."""

		haveRead = self.db.cursor()
		haveRead.execute('SELECT id FROM tweets WHERE id = ?', (str(tweetId),))
		haveRead = haveRead.fetchone()

		self.logger.debug('Looking for tweet %s: %sfound.', tweetId, '' if haveRead else 'not ')
		return haveRead != None

	def countTweets(self, userScreenName = None, reason = None):
		"""Count all tweets or all tweets by reason and/or user."""

		counter = self.db.cursor()

		if userScreenName and reason:
			counter.execute(
				'SELECT COUNT(id) AS count FROM tweets WHERE user_screen_name = ? AND reason = ?',
				(str(userScreenName), str(reason))
			)
		elif userScreenName:
			counter.execute(
				'SELECT COUNT(id) AS count FROM tweets WHERE user_screen_name = ?',
				(str(userScreenName),)
			)
		elif reason:
			counter.execute(
				'SELECT COUNT(id) AS count FROM tweets WHERE reason = ?',
				(str(reason),)
			)
		else:
			counter.execute('SELECT COUNT(id) AS count FROM tweets')

		counter = counter.fetchone()

		self.logger.debug(
			'Counting tweets%s%s: %s',
			' from @' + userScreenName if userScreenName else '',
			', reason=' + reason if reason else '',
			counter['count']
		)

		return counter['count']




	def initAdvisors(self, listSlug):
		"""Fetch list of advisors from Twitter."""
		self.advisors = []
		for user in self.twitter.list_members(self.me.screen_name, listSlug):
			self.advisors.append(str(user.id))
		self.logger.debug('Having %s advisors (list "%s").', len(self.advisors), listSlug)

	def initFollowers(self):
		"""Load followers from database."""
		followers = self.db.cursor()
		followers.execute('SELECT id FROM followers WHERE state > 0')
		self.followers = []
		for follower in followers.fetchall():
			self.followers.append(str(follower['id']))
		self.logger.debug('Having %s followers.', len(self.followers))

	def initFriends(self):
		"""Load friends from database."""
		friends = self.db.cursor()
		friends.execute('SELECT id FROM friends WHERE state > 0')
		self.friends = []
		for friend in friends.fetchall():
			self.friends.append(str(friend['id']))
		self.logger.debug('Having %s friends (I follow).', len(self.friends))




	def houseKeeping(self):
		"""Perform housekeeping actions."""

		if not self.acquireLock():
			return

		houseKeepingActions = [
			self.fetchFollowersFromTwitter,
			self.fetchFriendsFromTwitter
		]

		self.logger.info('Housekeeping!')
		startTime = datetime.now()
		for houseKeepingAction in houseKeepingActions:
			try:
				houseKeepingAction()
			except Exception as e:
				self.logger.exception('Exception during housekeeping.')

		self.logger.info('Housekeeping done, took: %s', datetime.now() - startTime)
		self.returnLock()

	def fetchFollowersFromTwitter(self):
		startTime = datetime.now()
		limbo = self.db.cursor()
		limbo.execute('UPDATE followers SET state = 2 WHERE state = 1')
		self.db.commit()
		self.logger.info('Having %s followers in limbo, updating with Twitter, this may take a while...', limbo.rowcount)
		for follower in self.twitter.followers():
			self.logger.debug('Adding follower %s @%s to database.', follower.id, follower.screen_name)
			self.db.cursor().execute(
				'INSERT OR REPLACE INTO followers (id,screen_name,state) VALUES (?,?,?)',
				(str(follower.id), str(follower.screen_name), 1)
			)
			self.db.commit()

		garbage = self.db.cursor()
		garbage.execute('UPDATE followers SET state = 0 WHERE state = 2')
		self.db.commit()
		self.logger.info(
			'Fetching followers done, lost %s followers, took: %s',
			garbage.rowcount, datetime.now() - startTime
		)
		self.initFollowers()

	def fetchFriendsFromTwitter(self):
		startTime = datetime.now()
		limbo = self.db.cursor()
		limbo.execute('UPDATE friends SET state = 2 WHERE state = 1')
		self.db.commit()
		self.logger.info('Having %s friends in limbo, updating with Twitter, this may take a while...', limbo.rowcount)

		for friend in self.twitter.friends():
			self.logger.debug('Adding friend %s @%s to database.', friend.id, friend.screen_name)
			self.db.cursor().execute(
				'INSERT OR REPLACE INTO friends (id,screen_name,state) VALUES (?,?,?)',
				(str(friend.id), str(friend.screen_name), 1)
			)
			self.db.commit()

		garbage = self.db.cursor()
		garbage.execute('UPDATE friends SET state = 0 WHERE state = 2')
		self.db.commit()
		self.logger.info('Fetching friends done, lost %s friends, took: %s', garbage.rowcount, datetime.now() - startTime)
		self.initFriends()




	def readMentions(self, items = 20):
		"""Read latest mentions."""

		if not self.acquireLock():
			return

		startTime = datetime.now()
		self.logger.info('Reading mentions at %s',  str(startTime))
		try:
			for tweet in self.twitter.mentions_timeline(items):
				if self.readMention(tweet):
					pass
		except Exception as e:
			self.logger.exception('Exception while reading mentions.')
		self.logger.info('Reading mentions took: %s, bye!', datetime.now() - startTime)
		self.returnLock()

	def readMention(self, tweet):
		"""Read a single mention and apply actions."""

		tweetLog = '@' + str(tweet.user.screen_name) + '/' + str(tweet.id)

		if self.haveReadTweet(tweet.id):
			self.logger.info('%s read before.', tweetLog)
			return False ## because "not read again"

		appliedAction = 'readMention'

		for action in [ self.adviceAction, self.retweetAction ]:
			if action(tweet):
				appliedAction = action.__name__
				break

		self.logger.info('%s applied %s.', tweetLog, appliedAction)

		self.rememberTweet(tweet.id, tweet.user.screen_name, appliedAction)
		return True ## because "read this time"




	def adviceAction(self, tweet):

		if not str(tweet.user.id) in self.advisors:
			return False ## not an advisor

		message = str(tweet.text)
		trigger = str('@' + self.me.screen_name + '!').lower()

		if not message.lower().startswith(trigger):
			return False ## not an advice

		## strip trigger from message to get the spelled advice
		advice = message[len(trigger):].strip()

		## advice: disable retweet feature on the fly
		if advice.lower() == 'geh schlafen!':
			self.logger.info(
				'Taking advice "%s" from %s.', advice, tweet.user.screen_name
			)

			self.acquireLock(self.sleepFile)

			if self.doReplying:
				self.twitter.update_status(
					in_reply_to_status_id = tweet.id,
					status = 'Ok @' + tweet.user.screen_name + ', ich gehe schlafen und retweete eine Weile nicht mehr... (Automatische Antwort)'
				)
			return True ## took advice

		## advice: enable retweet feature on the fly
		if advice.lower() == 'wach auf!':
			self.logger.info(
				'Taking advice "%s" from %s.', advice, tweet.user.screen_name
			)

			self.returnLock(self.sleepFile)

			if self.doReplying:
				self.twitter.update_status(
					in_reply_to_status_id = tweet.id,
					status = 'Ok @' + tweet.user.screen_name + ', ich wache auf und retweete gleich wieder... (Automatische Antwort)'
				)
			return True ## took advice

		return False ## did not take advice


	def retweetAction(self, tweet):

		if self.isLocked(self.sleepFile):
			self.logger.debug('I am sleeping, no retweet action.')
			return False

		if str(tweet.user.screen_name) == str(self.me.screen_name):
			self.logger.debug('@%s is me, no retweet.', tweet.user.screen_name)
			return False

		if str(tweet.user.protected) == 'True':
			self.logger.debug('@%s is protected, no retweet.', tweet.user.screen_name)
			return False

		if str(tweet.in_reply_to_status_id_str) != 'None':
			self.logger.debug('@%s wrote reply, no retweet.', tweet.user.screen_name)
			return False

		if str(tweet.user.id) not in self.followers:
			self.logger.debug('@%s is not following, no retweet.', tweet.user.screen_name)
			return False

		self.logger.debug(
			'@%s retweeting.%s',
			tweet.user.screen_name,
			'' if self.doRetweets else ' (not really)'
		)

		if self.doRetweets:
			self.twitter.retweet(tweet.id)

		return True


##
##
##
##

import tempfile
from unittest import mock, TestCase, TestLoader, TestResult, TestSuite, TextTestRunner

class KarlsruherTest(TestCase):

	@staticmethod
	def getTestSuite():
		testSuite = TestSuite()
		testSuite.addTest(TestLoader().loadTestsFromTestCase(KarlsruherTest))
		return testSuite

	@staticmethod
	def runVerboseAndExit():
		TextTestRunner(failfast = True).run(KarlsruherTest.getTestSuite())
		exit(0)

	@staticmethod
	def runSilent():
		testresult = TestResult()
		testresult.failfast = True
		KarlsruherTest.getTestSuite().run(testresult)
		return 0 == len(testresult.errors) == len(testresult.failures)


	## The bot to be tested
	bot = None

	## Testdata
	me = None
	advisor = None
	follower = None
	friend = None
	unknown = None
	tweet = None


	def setUp(self):
		self.me = mock.Mock(id = 123, screen_name = 'MockBot')
		self.advisor = mock.Mock(id = 4, screen_name = 'advisor')
		self.follower = mock.Mock(id = 5, screen_name = 'follower')
		self.friend = mock.Mock(id = 6, screen_name = 'friend')
		self.unknown = mock.Mock(id = 7, screen_name = 'unknown')
		self.tweet = mock.Mock(
			id = 4711, user = self.unknown,
			in_reply_to_status_id_str = None,
			text = 'Just mentioning @MockBot for no reason.'
		)
		## configure instance with mocks
		self.bot = Karlsruher(
			workDir = tempfile.gettempdir(),
			database = ':memory:',
			twitterClient = mock.Mock(
				me = mock.MagicMock(return_value=self.me),
				list_members = mock.MagicMock(return_value=[self.advisor]),
				followers = mock.MagicMock(return_value=[self.follower,self.advisor]),
				friends = mock.MagicMock(return_value=[self.friend]),
				update_status = mock.Mock(),
				retweet = mock.Mock(),
			)
		)

	def tearDown(self):
		self.bot.returnLock()
		self.bot.returnLock(self.bot.sleepFile)


	def test_000_setup_ok(self):
		self.assertEqual(0, self.bot.countTweets())
		self.assertEqual(1, self.bot.twitter.me.call_count)
		self.assertEqual(self.bot.me.screen_name, 'MockBot')
		self.assertEqual(1, self.bot.twitter.list_members.call_count)
		self.assertEqual(1, len(self.bot.advisors))
		self.assertEqual(0, len(self.bot.followers))
		self.assertEqual(0, len(self.bot.friends))
		self.assertFalse(self.bot.isLocked())
		self.assertFalse(self.bot.isLocked(self.bot.sleepFile))

	def test_001_can_lock_and_unlock(self):
		"""Ensure locking mechanics work."""
		self.assertTrue(self.bot.acquireLock())
		self.assertTrue(self.bot.isLocked())
		self.assertFalse(self.bot.acquireLock())
		self.bot.returnLock()
		self.assertFalse(self.bot.isLocked())

	def test_002_can_lock_and_unlock_file(self):
		"""Ensure locking mechanics work."""
		self.assertTrue(self.bot.acquireLock(self.bot.sleepFile))
		self.assertTrue(self.bot.isLocked(self.bot.sleepFile))
		self.assertFalse(self.bot.acquireLock(self.bot.sleepFile))
		self.bot.returnLock(self.bot.sleepFile)
		self.assertFalse(self.bot.isLocked(self.bot.sleepFile))

	def test_003_can_do_housekeeping(self):
		"""Ensure housekeeping works."""
		self.bot.houseKeeping()
		self.assertEqual(1, len(self.bot.advisors))
		self.assertEqual(2, len(self.bot.followers))
		self.assertEqual(1, len(self.bot.friends))
		self.assertTrue(str(self.advisor.id) in self.bot.advisors)
		self.assertTrue(str(self.advisor.id) in self.bot.followers)
		self.assertTrue(str(self.follower.id) in self.bot.followers)
		self.assertTrue(str(self.friend.id) in self.bot.friends)
		self.assertFalse(str(self.unknown.id) in self.bot.advisors)
		self.assertFalse(str(self.unknown.id) in self.bot.followers)
		self.assertFalse(str(self.unknown.id) in self.bot.friends)

	def test_101_can_remember_and_count_tweets(self):
		"""Ensure tweet database works."""
		self.bot.rememberTweet(1, 'user', 'A')
		self.bot.rememberTweet(2, 'other', 'B')
		self.bot.rememberTweet(3, 'user', 'C')
		self.assertEqual(3, self.bot.countTweets())
		self.assertFalse(self.bot.haveReadTweet(7))
		self.assertTrue(self.bot.haveReadTweet(1))
		self.assertTrue(self.bot.haveReadTweet(2))
		self.assertTrue(self.bot.haveReadTweet(3))
		self.assertEqual(1, self.bot.countTweets(reason='A'))
		self.assertEqual(1, self.bot.countTweets(reason='B'))
		self.assertEqual(1, self.bot.countTweets(reason='C', userScreenName='user'))
		self.assertEqual(0, self.bot.countTweets(reason='D'))
		self.assertEqual(2, self.bot.countTweets(userScreenName='user'))
		self.assertEqual(1, self.bot.countTweets(userScreenName='other'))
		self.assertEqual(0, self.bot.countTweets(reason='D',userScreenName='none'))

	def test_201_read_mention_only_once(self):
		"""Ensure to read and act only once per tweet."""
		self.tweet.user = self.follower
		self.assertTrue(self.bot.readMention(self.tweet))
		self.assertFalse(self.bot.readMention(self.tweet))

	def test_301_advice_ignore_from_non_advisors(self):
		"""Ensure to not take advices from arbitrary users."""
		self.tweet.user = self.unknown
		self.tweet.text = '@MoCkBoT! gEh scHlafen!'
		self.assertFalse(self.bot.adviceAction(self.tweet))

	def test_302_advice_sleep(self):
		"""Ensure to accept an advice to sleep."""
		self.tweet.user = self.advisor
		self.tweet.text = '@MoCkBoT! gEh scHlafen!'
		self.assertTrue(self.bot.adviceAction(self.tweet))
		self.assertTrue(self.bot.isLocked(self.bot.sleepFile))

	def test_303_advice_wakeup(self):
		"""Ensure to accept an advice to wake up."""
		self.assertTrue(self.bot.acquireLock(self.bot.sleepFile))
		self.assertTrue(self.bot.isLocked(self.bot.sleepFile))
		self.tweet.user = self.advisor
		self.tweet.text = '@MoCkBoT! wAcH aUf!'
		self.assertTrue(self.bot.adviceAction(self.tweet))
		self.assertFalse(self.bot.isLocked(self.bot.sleepFile))

	def test_501_retweet_follower(self):
		"""Ensure to retweet followers."""
		self.bot.houseKeeping()
		self.bot.doRetweets = True
		self.tweet.user = self.follower
		self.assertTrue(self.bot.retweetAction(self.tweet))
		self.assertEqual(1, self.bot.twitter.retweet.call_count)

	def test_502_retweet_follower(self):
		"""Ensure to retweet followers."""
		self.bot.houseKeeping()
		self.bot.doRetweets = False
		self.tweet.user = self.follower
		self.assertTrue(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_503_retweet_not_self(self):
		"""Ensure to not retweet self."""
		self.bot.houseKeeping()
		self.bot.doRetweets = True
		self.tweet.user = self.me
		self.assertFalse(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_504_retweet_not_non_followers(self):
		"""Ensure to not retweet non-followers."""
		self.bot.houseKeeping()
		self.bot.doRetweets = True
		self.tweet.user = self.unknown
		self.assertFalse(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_505_retweet_not_protected(self):
		"""Ensure to not retweet protected users."""
		self.bot.houseKeeping()
		self.bot.doRetweets = True
		for user in [ self.follower, self.advisor ]:
			self.tweet.user = user
			self.tweet.user.protected = True
			self.assertFalse(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_506_retweet_not_replies(self):
		"""Ensure to not retweet replies."""
		self.bot.houseKeeping()
		self.bot.doRetweets = True
		for user in [
			self.me, self.unknown,
			self.follower, self.advisor
		]:
			self.tweet.user = user
			self.tweet.in_reply_to_status_id_str = '7500'
			self.assertFalse(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)

	def test_507_retweet_not_during_sleep(self):
		"""Ensure to not retweet during sleep."""
		self.bot.houseKeeping()
		self.bot.doRetweets = True
		self.tweet.user = self.follower
		self.assertTrue(self.bot.acquireLock(self.bot.sleepFile))
		self.assertFalse(self.bot.retweetAction(self.tweet))
		self.assertEqual(0, self.bot.twitter.retweet.call_count)


##
##
##
##


class TwitterClient:

	logger = None
	api = None

	def __init__(self, runDir):

		self.logger = logging.getLogger(__name__)

		credentials = runDir + '/credentials.py'

		if not fs.isfile(credentials):
			self.logger.error('Ooops, missing file: %s', credentials)
			raise Exception(
				'Credentials missing!', credentials,
				'(Please use the provided example file and your own API keys to create this file.)'
			)

		self.logger.debug('Using credentials from %s.', credentials)
		from credentials import TWITTER_CONSUMER_KEY
		from credentials import TWITTER_CONSUMER_SECRET
		from credentials import TWITTER_ACCESS_KEY
		from credentials import TWITTER_ACCESS_SECRET

		self.logger.debug('Connecting to Twitter...')
		oauth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
		oauth.set_access_token(TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET)
		self.api = tweepy.API(
			oauth, compression = True,
			wait_on_rate_limit = True, wait_on_rate_limit_notify = True
		)

	def me(self):
		me = self.api.me()
		self.logger.debug('me() response: %s', me)
		return me

	def mentions_timeline(self, items = 20):
		self.api.mentions_timeline.pagination_mode = 'cursor'
		for mention in tweepy.Cursor(self.api.mentions_timeline).items(items):
			yield mention

	def list_members(self, owner, slug):
		self.api.list_members.pagination_mode = 'cursor'
		for member in tweepy.Cursor(self.api.list_members, owner, slug).items():
			yield member

	def followers(self):
		self.api.followers.pagination_mode = 'cursor'
		for follower in tweepy.Cursor(self.api.followers).items():
			yield follower

	def friends(self):
		self.api.friends.pagination_mode = 'cursor'
		for friend in tweepy.Cursor(self.api.friends).items():
			yield friend

	def retweet(self, tweet):
		try:
			response = self.api.retweet(tweet.id)
			self.logger.debug('retweet() response: %s', response)
			return response
		except Exception as e:
			self.logger.exception('API call "retweet".')
		return None

	def update_status(self, status, in_reply_to_status_id = None):
		try:
			if not in_reply_to_status_id:
				response = self.api.update_status(status = status)
			else:
				response = self.api.update_status(
					status = status,
					in_reply_to_status_id = in_reply_to_status_id
				)
			self.logger.debug('update_status() response: %s', response)
			return response
		except Exception as e:
			self.logger.exception('API call "update_status".')
		return None

##
##
##
##


class CommandLine:

	"""The @Karlsruher Retweet Robot

  * Retweet followers (but not any tweet)
  * Listen for advices (remote commands)

  Run Modes:

	-test	Only perform self-tests verbosely and exit.

  or

	-read	Read timelines and perform activities (silently)
		This reads mentions only for now. All read tweets will be
		remembered and won't be read again.

    and additionally

 	-talk	All of -tweet, -reply, -retweet
	-retweet	Send retweets, otherwise just log
	-reply	Send replies (responses), otherwise just log
	-tweet	Send tweets (status messages), otherwise just log

	# Cronjob (all 5 minutes):
	*/5 * * * * /path/to/karlsruher/run.py -read -talk >/dev/null 2>&1

  or
	-housekeeping	Only perform housekeeping tasks and exit.
		This fetches followers and friends from Twitter.
		Due to API Rate Limits, housekeeping is throttled
		and takes up to 1 hour per 1000 followers.

	# Cronjob (run once per day):
	3 3 * * * /path/to/karlsruher/run.py -housekeeping >/dev/null 2>&1


  -help		what you are reading right now

  Use "-debug" to raise overall logging level."""


	@staticmethod
	def run(workDir, arguments):

		if '-test' in arguments:
			logging.basicConfig(
				level = logging.DEBUG if '-debug' in arguments else logging.ERROR,
				format = '%(levelname)-5.5s [%(funcName)s]: %(message)s',
				handlers = [logging.StreamHandler()]
			)
			KarlsruherTest.runVerboseAndExit()

		if not KarlsruherTest.runSilent():
			print("Selftest failed, aborting.")
			print("Run again with -test -debug to see what fails.")
			exit(1)

		logging.basicConfig(
			level = logging.DEBUG if '-debug' in arguments else logging.INFO,
			format = '%(asctime)s %(levelname)-5.5s [%(module)s#%(funcName)s]: %(message)s',
			handlers = [logging.StreamHandler()]
		)

		if '-read' in arguments:
			k = Karlsruher(workDir)
			k.doTweeting = '-tweet' in arguments or '-talk' in arguments
			k.doReplying = '-reply' in arguments or '-talk' in arguments
			k.doRetweets = '-retweet' in arguments or '-talk' in arguments
			k.readMentions()
			exit(0)

		if '-housekeeping' in arguments:
			k = Karlsruher(workDir)
			k.houseKeeping()
			exit(0)

		print(CommandLine.__doc__)
		exit(0)
