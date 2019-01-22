#!/usr/bin/env python3

## Karlsruher Retweet Bot https://github.com/schlind/Karlsruher


## Developed and tested with
from sys import version_info as python_version
assert python_version >= (3,)
## Import dependencies
from datetime import datetime
from os import environ as env, path as fs, remove
from sys import argv, exit
import logging
import sqlite3
import tweepy
from unittest import mock, TestCase, TestLoader, TestResult, TestSuite, TextTestRunner


## Implementation
class Karlsruher:
	"""The @Karlsruher Retweet Robot
+ Retweet followers (but not any tweet)
+ Listen for advices (special mentions) from advisors (special users):

Run Modes:

  -test		Only perform tests verbosely and exit.

  -housekeeping	Only perform housekeeping tasks and exit.
	This fetches followers and friends from Twitter.
	Due to API Rate Limits, housekeeping is throttled
	and takes up to 1 hour per 1000 followers.

	# Cronjob:
	3 3 * * * /karlsruher.py -housekeeping >> /karlsruher.log 2>&1

  -read		Read timelines and perform activities (silently)
	This reads mentions only for now. All read tweets will be
	remembered and won't be read again.

  -talk			All of -tweet, -reply, -retweet
  -tweet		Send tweets (status messages), otherwise just log
  -reply		Send replies (responses), otherwise just log
  -retweet		Send retweets, otherwise just log

	# Cronjob:
	*/5 * * * * /karlsruher.py -read -talk >> /karlsruher.log 2>&1

  -help		what you are reading right now

  Use "-debug" to raise overall logging level."""


	@staticmethod
	def main(arguments):

		selftest = TestSuite()
		selftest.addTest(TestLoader().loadTestsFromTestCase(KarlsruherTest))

		if '-test' in arguments:
			## Configure logging for verbose test-only run.
			logging.basicConfig(
				level = logging.DEBUG if '-debug' in arguments else logging.INFO,
				format = '%(levelname)-5.5s [%(funcName)s]: %(message)s',
				handlers=[logging.StreamHandler()]
			)
			## Run tests, print result & exit.
			TextTestRunner(failfast = True).run(selftest)
			exit(0)

		## Run self-test silently and exit when a test fails.
		testresult = TestResult()
		testresult.failfast = True
		selftest.run(testresult)
		if not 0 == len(testresult.errors) == len(testresult.failures):
			print("Selftest failed, aborting.")
			print("Run again with -test -debug to see what fails.")
			exit(1)

		## Configure logging for production log.
		logging.basicConfig(
			level = logging.DEBUG if '-debug' in arguments else logging.INFO,
			format = '%(asctime)s %(levelname)-5.5s [%(module)s#%(funcName)s]: %(message)s',
			handlers=[logging.StreamHandler()]
		)

		if '-read' in arguments:
			bot = Karlsruher()
			bot.doTweeting = '-tweet' in arguments or '-talk' in arguments
			bot.doReplying = '-reply' in arguments or '-talk' in arguments
			bot.doRetweets = '-retweet' in arguments or '-talk' in arguments
			bot.readMentions()
			exit(0)
		if '-housekeeping' in arguments:
			bot = Karlsruher()
			bot.houseKeeping()
			exit(0)

		print(Karlsruher.__doc__)
		exit(0)


	## Instance

	homeDirectory = fs.dirname(fs.realpath(__file__))

	databaseFile = None
	lockFile = None
	sleepFile = None

	me = None
	logger = None
	twitter = None
	db = None

	doHouseKeeping = False
	doRetweets = False
	doReplying = False
	doTweeting = False

	advisors = []
	followers = []
	friends = []




	def __init__(self, twitter = None, credentials = None, database = None):
		"""
		Initialize connections to and load required data
		from Twitter and database.
		"""
		self.logger = logging.getLogger(__name__)
		self.logger.debug('%s %s', __class__, datetime.now())

		try:
			self.initTwitterAndBotName(twitter, credentials)
			self.logger.info('Hello, my name is %s.', self.me.screen_name)
			self.initDatabase(database)
			self.initAdvisors()
			self.initFollowers()
			self.initFriends()
		except Exception as e:
			self.logger.exception('Exception during initialization.')
			raise e

		self.sleepFile = self.homeDirectory + '/.sleep.' + self.me.screen_name.lower()
		self.lockFile = self.homeDirectory + '/.lock.' + self.me.screen_name.lower()




	def initTwitterAndBotName(self, tweepyAPI = None, credentials = None):
		"""
		Assign a specified tweepy.API instance or create one.
		Fetch the related account's user from API as self.me.
		"""

		if tweepyAPI:
			## Injected mock for testing, no real connection to Twitter.
			self.logger.debug('Using injected tweepyAPI instance.')
			self.twitter = tweepyAPI

		else:
			## Or check API keys and create Tweepy instance.
			self.logger.debug('Connecting to twitter.')

			if not credentials:
				credentials = self.homeDirectory + '/credentials.py'

			if not fs.isfile(credentials):
				self.logger.error('Ooops, missing file: %s', credentials)
				self.logger.info('Please use the .example and your own API keys to create this file.')
				exit(1)

			from credentials import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
			from credentials import TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET
			oauth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
			oauth.set_access_token(TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET)

			self.twitter = tweepy.API(
				oauth, compression = True,
				wait_on_rate_limit = True, wait_on_rate_limit_notify = True
			)

		self.logger.debug('Twitter connected, fetching me from API.')
		self.me = self.twitter.me()


	def tweet(self, text):
		self.logger.debug(
			'TWEET%s: %s.', '' if self.doTweeting else ' (not really)', text
		)
		if self.doTweeting:
			try:
				response = self.twitter.update_status(status = text)
				if response:
					self.logger.debug('Response: %s', response)
				return response
			except Exception as e:
				self.logger.exception('API call "update_status".')
		return None


	def reply(self, tweet, text):
		## Twitter want's replies to contain a mention of the origin user.
		## Really simple check that would not find "@mention!" e.g.
		if not '@' + str(tweet.user.screen_name) in text:
			self.logger.debug('Prefixing reply with @%s', tweet.user.screen_name)
			text = '@' + str(tweet.user.screen_name) + ' ' + text
		self.logger.debug(
			'REPLY%s to @%s/%s: %s',
			'' if self.doReplying else ' (not really)',
			tweet.user.screen_name, tweet.id, text
		)
		if self.doReplying:
			try:
				response = self.twitter.update_status(
					status = text, in_reply_to_status_id = tweet.id
				)
				if response:
					self.logger.debug('Response: %s', response)
				return response
			except Exception as e:
				self.logger.exception('API call "update_status".')
		return None


	def retweet(self, tweet):
		self.logger.debug(
			'RETWEET%s @%s/%s: %s',
			'' if self.doRetweets else ' (not really)',
			tweet.user.screen_name, tweet.id, tweet.text
		)
		if self.doRetweets:
			try:
				response = self.twitter.retweet(tweet.id)
				if response:
					self.logger.debug('Response: %s', response)
				return response
			except Exception as e:
				self.logger.exception('API call "retweet".')
		return None




	def initDatabase(self, database = None):
		"""Connect to database and create tables if needed."""
		if database:
			self.databaseFile = database
		else:
			self.databaseFile = self.homeDirectory + '/'+ self.me.screen_name.lower() + '.db'

		self.logger.debug('Using "%s" as database.', self.databaseFile)
		self.db = sqlite3.connect(self.databaseFile)
		self.db.row_factory = sqlite3.Row

		self.db.cursor().execute('CREATE TABLE IF NOT EXISTS tweets (id VARCHAR PRIMARY KEY, user_screen_name VARCHAR NOT NULL, reason VARCHAR NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
		self.db.commit()

		self.db.cursor().execute('CREATE TABLE IF NOT EXISTS followers (id VARCHAR PRIMARY KEY, screen_name VARCHAR NOT NULL, state INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
		self.db.commit()

		self.db.cursor().execute('CREATE TABLE IF NOT EXISTS friends (id VARCHAR PRIMARY KEY, screen_name VARCHAR NOT NULL, state INTEGER DEFAULT 0, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
		self.db.commit()


	def rememberTweet(self, tweetId, userScreenName, reason = 'non reason given'):
		"""Store a tweet's id, user's screen_name and a reason to database."""
		self.logger.debug('Remembering tweet %s', tweetId)
		remember = self.db.cursor()
		remember.execute('INSERT OR IGNORE INTO tweets (id,user_screen_name,reason) VALUES (?,?,?)', (str(tweetId),str(userScreenName),str(reason)))
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
		self.logger.debug('Counting tweets %s %s', userScreenName, reason)
		counter = self.db.cursor()
		count = 'SELECT COUNT(id) AS count FROM tweets '
		if userScreenName and reason:
			counter.execute(count + 'WHERE user_screen_name = ? AND reason = ?', (str(userScreenName), str(reason)))
		elif userScreenName:
			counter.execute(count + 'WHERE user_screen_name = ?', (str(userScreenName),))
		elif reason:
			counter.execute(count + 'WHERE reason = ?', (str(reason),))
		else:
			counter.execute(count)
		return counter.fetchone()['count']




	def initAdvisors(self):
		"""Fetch list of advisors from Twitter."""
		self.advisors = []
		listName = 'advisors'
		try:
			for user in self.twitter.list_members(self.me.screen_name, listName):
				self.advisors.append(str(user.id))
		except Exception as e:
			self.logger.exception('API call "list_members".')

		self.logger.debug('I have %s advisors', len(self.advisors))


	def initFollowers(self):
		"""Load followers from database."""
		followers = self.db.cursor()
		followers.execute('SELECT id FROM followers WHERE state = 1 OR state = 2')
		self.followers = []
		for follower in followers.fetchall():
			self.followers.append(str(follower['id']))

		self.logger.debug('I have %s followers.', len(self.followers))


	def fetchFollowersFromTwitter(self):
		"""
		Fetch followers from Twitter and store them in database.
		Due to API rate limitis, this may take up to 1 hour per 1000 followers.
		"""

		startTime = datetime.now()

		limbo = self.db.cursor()
		limbo.execute('UPDATE followers SET state = 2 WHERE state = 1')
		self.db.commit()
		self.logger.info('Having %s followers in limbo, updating with Twitter, this may take a while...', limbo.rowcount)

		self.logger.debug('Calling Twitter API and storing followers in DB.')
		self.twitter.followers.pagination_mode = 'cursor'
		for follower in tweepy.Cursor(self.twitter.followers).items():
			self.logger.debug('Adding follower %s %s to database.', follower.id, follower.screen_name)
			self.db.cursor().execute('INSERT OR REPLACE INTO followers (id,screen_name,state) VALUES (?,?,?)', (str(follower.id), str(follower.screen_name), 1))
			self.db.commit()

		garbage = self.db.cursor()
		garbage.execute('UPDATE followers SET state = 0 WHERE state = 2')
		self.db.commit()
		self.logger.info('Fetching followers done, lost %s followers, took: %s', garbage.rowcount, datetime.now() - startTime)
		self.initFollowers()


	def initFriends(self):
		"""Load friends from database."""
		self.friends = []
		notfollowing = []
		friends = self.db.cursor()
		friends.execute('SELECT id,screen_name FROM friends WHERE state = 1')
		for friend in friends.fetchall():
			self.friends.append(str(friend['id']))
			follower = self.db.cursor()
			follower.execute('SELECT id FROM followers WHERE state = 1 AND id = ?', (friend['id'],))
			if not follower.fetchone() and friend['id'] not in self.advisors:
				notfollowing.append(str(friend['screen_name']))

		self.logger.debug('I have %s friends, %s do not follow me.', len(self.friends), len(notfollowing))


	def fetchFriendsFromTwitter(self):
		"""
		Fetch friends from Twitter and store them in database.
		"""

		startTime = datetime.now()

		limbo = self.db.cursor()
		limbo.execute('UPDATE friends SET state = 2 WHERE state = 1')
		self.db.commit()
		self.logger.info('Having %s friends in limbo, updating with Twitter, this may take a while...', limbo.rowcount)

		self.logger.debug('Calling Twitter API and storing friends in DB.')
		self.twitter.friends.pagination_mode = 'cursor'
		for friend in tweepy.Cursor(self.twitter.friends).items():
			self.logger.debug('Adding friend %s %s to database.', friend.id, friend.screen_name)
			self.db.cursor().execute('INSERT OR REPLACE INTO friends (id,screen_name,state) VALUES (?,?,?)', (str(friend.id), str(friend.screen_name), 1))
			self.db.commit()

		garbage = self.db.cursor()
		garbage.execute('UPDATE friends SET state = 0 WHERE state = 2')
		self.db.commit()
		self.logger.info('Fetching friends done, lost %s friends, took: %s', garbage.rowcount, datetime.now() - startTime)
		self.initFriends()




	def lock(self, lockFile = None):
		if not lockFile:
			lockFile = self.lockFile
		if fs.isfile(lockFile):
			self.logger.debug('Is locked: %s', lockFile)
			return False
		self.logger.debug('Locking: %s', lockFile)
		open(lockFile, 'a').close()
		return True

	def unlock(self, lockFile = None):
		if not lockFile:
			lockFile = self.lockFile
		self.logger.debug('Unlocking: %s', lockFile)
		if fs.isfile(lockFile):
			remove(lockFile)

	def isLocked(self, lockFile = None):
		if not lockFile:
			lockFile = self.lockFile
		if fs.isfile(lockFile):
			self.logger.debug('Is locked: %s', lockFile)
			return True
		return False




	def houseKeeping(self):
		"""
		Let the bot do housekeeping.

		Housekeeping performs clean-up and updating tasks
		that are not triggered by a Twitter timeline.

		Run with -housekeeping on the command line.
		"""
		if not self.lock():
			return

		self.logger.info('Housekeeping!')
		startTime = datetime.now()
		try:
			self.fetchFollowersFromTwitter()
			self.fetchFriendsFromTwitter()
		except Exception as e:
			self.logger.exception('Exception during housekeeping.')

		self.logger.info('Housekeeping done, took: %s', datetime.now() - startTime)
		self.unlock()




	def readMentions(self):
		"""
		Read mentions and run activities.
		Run with -read on the command line.
		"""
		if not self.lock():
			return

		startTime = datetime.now()
		self.logger.info(
			'Reading mentions %s & %s & %s & %s.', str(startTime),
			'retweeting' if self.doRetweets else 'not retweeting',
			'replying' if self.doReplying else 'not replying',
			'tweeting' if self.doTweeting else 'not tweeting'
		)

		try:
			for tweet in self.twitter.mentions_timeline():
				self.readMention(tweet)
		except Exception as e:
			self.logger.exception('Exception when reading mentions.')

		self.logger.info('Reading mentions took: %s, bye!', datetime.now() - startTime)
		self.unlock()


	def readMention(self, tweet):
		"""Read a single mention and delegate further action."""

		read = 'Read tweet @' + str(tweet.user.screen_name) + '/' + str(tweet.id)

		if self.haveReadTweet(tweet.id):
			self.logger.info('%s before.', read)
			return False

		try:
			for actionMethod in [ self.adviceAction, self.retweetAction ]:
				if actionMethod(tweet):
					self.rememberTweet(tweet.id, tweet.user.screen_name, actionMethod.__name__)
					self.logger.info('%s and remembered %s.', read, actionMethod.__name__)
					return True
		except Exception as e:
			self.logger.exception('Exceptional mention: %s', read)

		self.rememberTweet(tweet.id, tweet.user.screen_name, 'readMention')
		self.logger.info('%s remembered.', read)
		return True


	def adviceAction(self, tweet):
		"""
		Perform the logic to take an advice.

			'@Botname! [advice]'

		"""
		if not str(tweet.user.id) in self.advisors:
			return False

		trigger = str('@' + self.me.screen_name + '!').lower()
		message = str(tweet.text)

		if not message.lower().startswith(trigger):
			return False

		advice = message[len(trigger):].strip()

		try:

			if advice.lower() == 'geh schlafen!':
				self.logger.info('Taking advice "%s" from %s.', advice, tweet.user.screen_name)
				self.lock(self.sleepFile)
				self.reply(tweet, 'Ok, ich gehe schlafen. (Automatische Antwort)')
				self.tweet('Ich retweete vorübergehend nicht mehr. (Automatische Nachricht)')
				return True

			if advice.lower() == 'wach auf!':
				self.logger.info('Taking advice "%s" from %s.', advice, tweet.user.screen_name)
				self.unlock(self.sleepFile)
				self.reply(tweet, 'Ok, ich wache auf. (Automatische Antwort)')
				self.tweet('Ich retweete jetzt wieder. (Automatische Nachricht)')
				return True

		except Exception as e:
			self.logger.exception('Exception while taking advice.')

		return False


	def retweetAction(self, tweet):
		"""
		Perform the retweet logic.
		As long as the bot is not sleeping it retweets *all* its mentions.
		There are exceptions to this as they are implemented here.
		"""
		if self.isLocked(self.sleepFile):
			self.logger.debug('I am sleeping, no retweet action.')
			return False

		if str(tweet.user.screen_name) == str(self.me.screen_name):
			self.logger.debug('@%s is me! Not retweeting.', tweet.user.screen_name)
			return False

		if str(tweet.user.protected) == 'True':
			self.logger.debug('@%s is private, no retweet.', tweet.user.screen_name)
			return False

		if str(tweet.in_reply_to_status_id_str) != 'None':
			self.logger.debug('@%s wrote reply, no retweet.', tweet.user.screen_name)
			return False

		if str(tweet.user.id) not in self.followers:
			self.logger.debug('@%s not following, no retweet.', tweet.user.screen_name)
			return False

		retweet = self.retweet(tweet)
		if retweet:
			self.logger.debug('Response: retweet=[%s]', retweet)

		return True




## Test
class KarlsruherTest(TestCase):

	## Testdata.
	testUnknownUser = None
	testMe = None
	testAdvisor = None
	testFollower = None
	testFriend = None
	testTweet = None
	testFile = None

	## A bot set up to be tested.
	bot = None

	def setUp(self):
		self.testUnknownUser = mock.Mock(id = 111, screen_name = 'unknown')
		self.testMe = mock.Mock(id = 222, screen_name = 'MockBot')
		self.testAdvisor = mock.Mock(id = 333, screen_name = 'advisor')
		self.testFollower = mock.Mock(id = 444, screen_name = 'follower')
		self.testFriend = mock.Mock(id = 555, screen_name = 'friend')
		self.testTweet = mock.Mock(
			id = 4711, user = self.testUnknownUser,
			in_reply_to_status_id_str = None,
			text = 'Just mentioning @MockBot for no reason.'
		)
		tweepyAPIMock = mock.Mock(
			## tweepy.api.me() returns a Twitter user object.
			me = mock.MagicMock(return_value = self.testMe),
			## tweepy.api.list_members() returns a list of Twitter user objects.
			list_members = mock.MagicMock( return_value = [ self.testAdvisor ]),
			## tweepy.api.followers() returns a list of Twitter user objects.
			# unused: test uses mocked cursor
			#followers = mock.MagicMock( return_value = [ self.testFollower, self.testAdvisor ]),
			## tweepy.api.friends() returns a list of Twitter user objects.
			# unused: test uses mocked cursor
			#friends = mock.MagicMock( return_value = [ self.testFriend ]),
		)
		testBot = Karlsruher(twitter = tweepyAPIMock, database = ':memory:')

		data = testBot.db.cursor()
		data.execute('INSERT INTO followers (id,screen_name,state) VALUES (?,?,?)', (str(self.testFollower.id), str(self.testFollower.screen_name), 1))
		data.execute('INSERT INTO followers (id,screen_name,state) VALUES (?,?,?)', (str(self.testAdvisor.id), str(self.testAdvisor.screen_name), 1))
		data.execute('INSERT INTO friends (id,screen_name,state) VALUES (?,?,?)', (str(self.testFriend.id), str(self.testFriend.screen_name), 1))
		testBot.db.commit()
		testBot.initFollowers()
		testBot.initFriends()

		self.bot = testBot


	def tearDown(self):
		bot = self.bot
		bot.unlock()
		bot.unlock(bot.sleepFile)
		bot.unlock(bot.databaseFile)

	def test_can_init_bot(self):
		"""Ensure initialization works on the happy path."""
		bot = self.bot
		self.assertEqual(1, bot.twitter.me.call_count)
		self.assertEqual(bot.me.screen_name, 'MockBot')

	def test_bot_can_init_db(self):
		"""Ensure to have a database."""
		bot = self.bot
		self.assertEqual(0, bot.countTweets())

	def test_bot_can_init_advisors(self):
		"""Ensure to read advisors from list."""
		bot = self.bot
		self.assertTrue(str(self.testAdvisor.id) in bot.advisors)
		self.assertFalse(str(7) in bot.advisors)

	def test_bot_can_init_followers(self):
		"""Ensure to read followers from database."""
		bot = self.bot
		self.assertEqual(2, len(bot.followers))
		self.assertTrue(str(self.testAdvisor.id) in bot.followers)
		self.assertTrue(str(self.testFollower.id) in bot.followers)

	def test_bot_can_keep_track_of_followers(self):
		"""Ensure to keep track of followers."""
		bot = self.bot
		real_tweepy_Cursor_items = tweepy.Cursor.items
		tweepy.Cursor.items = mock.MagicMock(
			return_value = [ self.testFollower ]
		)
		bot.fetchFollowersFromTwitter()
		self.assertEqual(1, len(bot.followers))
		## Loose 1st, get 3 new...
		tweepy.Cursor.items = mock.MagicMock(
			return_value = [
				mock.Mock(id = 4, screen_name = 'follower2'),
				mock.Mock(id = 5, screen_name = 'follower3'),
				mock.Mock(id = 6, screen_name = 'follower4')
			]
		)
		bot.fetchFollowersFromTwitter()
		self.assertEqual(3, len(bot.followers))
		tweepy.Cursor.items = real_tweepy_Cursor_items

	def test_bot_can_init_friends(self):
		"""Ensure to read friends from database."""
		bot = self.bot
		self.assertEqual(1, len(bot.friends))

	def test_bot_can_keep_track_of_friends(self):
		"""Ensure to keep track of friends."""
		bot = self.bot
		real_tweepy_Cursor_items = tweepy.Cursor.items
		tweepy.Cursor.items = mock.MagicMock(
			return_value = [ self.testFriend ]
		)
		bot.fetchFriendsFromTwitter()
		self.assertEqual(1, len(bot.friends))
		## Loose 1st, get 3 new...
		tweepy.Cursor.items = mock.MagicMock(
			return_value = [
				mock.Mock(id = 4, screen_name = 'friend2'),
				mock.Mock(id = 5, screen_name = 'friend3')
			]
		)
		bot.fetchFriendsFromTwitter()
		self.assertEqual(2, len(bot.friends))
		tweepy.Cursor.items = real_tweepy_Cursor_items

	def test_can_do_tweet(self):
		bot = self.bot
		bot.doTweeting = False
		bot.tweet('test_can_do_tweet')
		self.assertEqual(0, bot.twitter.update_status.call_count)
		bot.doTweeting = True
		bot.tweet('test_can_do_tweet')
		self.assertEqual(1, bot.twitter.update_status.call_count)

	def test_can_do_reply(self):
		bot = self.bot
		bot.doReplying = False
		self.testTweet.user = self.testUnknownUser
		bot.reply(self.testTweet, 'test_can_do_reply')
		self.assertEqual(0, bot.twitter.update_status.call_count)
		bot.doReplying = True
		bot.reply(self.testTweet, 'test_can_do_reply')
		self.assertEqual(1, bot.twitter.update_status.call_count)

	def test_can_do_retweet(self):
		bot = self.bot
		bot.doRetweets = False
		self.testTweet.user = self.testUnknownUser
		bot.retweet(self.testTweet)
		self.assertEqual(0, bot.twitter.retweet.call_count)
		bot.doRetweets = True
		bot.retweet(self.testTweet)
		self.assertEqual(1, bot.twitter.retweet.call_count)

	def test_bot_can_remember_tweets(self):
		"""Ensure to remember tweets."""
		bot = self.bot
		bot.rememberTweet(1, 'u', 'A')
		bot.rememberTweet(2, 'x', 'B')
		bot.rememberTweet(3, 'u', 'C')
		self.assertEqual(3, bot.countTweets())
		self.assertFalse(bot.haveReadTweet(7))
		self.assertTrue(bot.haveReadTweet(1))
		self.assertTrue(bot.haveReadTweet(2))
		self.assertTrue(bot.haveReadTweet(3))
		self.assertEqual(1, bot.countTweets(reason='A'))
		self.assertEqual(1, bot.countTweets(reason='B'))
		self.assertEqual(1, bot.countTweets(reason='C', userScreenName='u'))
		self.assertEqual(0, bot.countTweets(reason='D'))
		self.assertEqual(2, bot.countTweets(userScreenName='u'))
		self.assertEqual(1, bot.countTweets(userScreenName='x'))
		self.assertEqual(0, bot.countTweets(reason='D',userScreenName='x'))

	def test_bot_can_lock_and_unlock(self):
		"""Ensure locking mechanics work as expected."""
		bot = self.bot
		self.assertFalse(bot.isLocked())
		self.assertTrue(bot.lock())
		self.assertTrue(bot.isLocked())
		self.assertFalse(bot.lock())

	def test_bot_doesnot_read_a_tweet_twice(self):
		"""Ensure to not read and act on the same tweet twice."""
		bot = self.bot
		self.testTweet.user = self.testFollower
		self.assertTrue(bot.readMention(self.testTweet))
		self.assertFalse(bot.readMention(self.testTweet))

	def test_bot_doesnot_take_advice_from_arbitrary_user(self):
		"""Ensure to not take advices from arbitrary users."""
		bot = self.bot
		self.testTweet.user = self.testUnknownUser
		self.testTweet.text = '@MoCkBoT! gEh scHlafen!'
		self.assertFalse(bot.adviceAction(self.testTweet))

	def test_bot_can_handle_advice_sleep(self):
		"""Ensure to accept advice to sleep."""
		bot = self.bot
		self.testTweet.user = self.testAdvisor
		self.testTweet.text = '@MoCkBoT! gEh scHlafen!'
		self.assertFalse(bot.isLocked(bot.sleepFile))
		self.assertTrue(bot.adviceAction(self.testTweet))
		self.assertTrue(bot.isLocked(bot.sleepFile))

	def test_bot_can_handle_advice_wakeup(self):
		"""Ensure to accept advice to wake up."""
		bot = self.bot
		bot.lock(bot.sleepFile)
		self.assertTrue(bot.isLocked(bot.sleepFile))
		self.testTweet.user = self.testAdvisor
		self.testTweet.text = '@MoCkBoT! wAcH aUf!'
		self.assertTrue(bot.adviceAction(self.testTweet))
		self.assertFalse(bot.isLocked(bot.sleepFile))

	def test_bot_can_retweet_follower(self):
		"""Ensure to retweet followers."""
		bot = self.bot
		bot.doRetweets = True
		self.testTweet.user = self.testFollower
		self.assertTrue(bot.retweetAction(self.testTweet))
		self.assertEqual(1, bot.twitter.retweet.call_count)

	def test_bot_doesnot_retweet_self(self):
		"""Ensure to not retweet self."""
		bot = self.bot
		bot.doRetweets = True
		self.testTweet.user = self.testMe
		self.assertFalse(bot.retweetAction(self.testTweet))
		self.assertEqual(0, bot.twitter.retweet.call_count)

	def test_bot_doesnot_retweet_non_followers(self):
		"""Ensure to not retweet non-followers."""
		bot = self.bot
		bot.doRetweets = True
		self.testTweet.user = self.testUnknownUser
		self.assertFalse(bot.retweetAction(self.testTweet))
		self.assertEqual(0, bot.twitter.retweet.call_count)

	def test_bot_doesnot_retweet_protected(self):
		"""Ensure to not retweet protected users."""
		bot = self.bot
		bot.doRetweets = True
		for user in [
			self.testFollower, self.testAdvisor
		]:
			self.testTweet.user = user
			self.testTweet.user.protected = True
			self.assertFalse(bot.retweetAction(self.testTweet))
		self.assertEqual(0, bot.twitter.retweet.call_count)

	def test_bot_doesnot_retweet_replies(self):
		"""Ensure to not retweet replies."""
		bot = self.bot
		bot.doRetweets = True
		for user in [
			self.testMe, self.testUnknownUser,
			self.testFollower, self.testAdvisor
		]:
			self.testTweet.user = user
			self.testTweet.in_reply_to_status_id_str = '7500'
			self.assertFalse(bot.retweetAction(self.testTweet))
		self.assertEqual(0, bot.twitter.retweet.call_count)

	def test_bot_doesnot_retweet_during_sleep(self):
		"""Ensure to not retweet during sleep."""
		bot = self.bot
		bot.lock(bot.sleepFile)
		bot.doRetweets = True
		self.testTweet.user = self.testFollower
		self.assertFalse(bot.retweetAction(self.testTweet))
		self.assertEqual(0, bot.twitter.retweet.call_count)




## Runtime
if not env.get('KARLSRUHER_SKIP_MAIN'):
	Karlsruher.main(argv)
## Feddich
