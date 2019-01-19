#!/usr/bin/env python3
##
## Karlsruher Retweet Bot https://github.com/schlind/Karlsruher
##
## Cronjob:
##	*/5 * * * * /path/to/karlsruher.py -talk >> /path/to/karlsruher.log 2>&1
##	42 0 * * * /path/to/karlsruher.py -housekeeping >> /path/to/karlsruher.log 2>&1
##


## Imports
from datetime import datetime
import logging
from os import path, remove
import sqlite3
from sys import version_info, argv, stdout, exit
import tweepy
from unittest import TestLoader, TestCase, TestResult, TestSuite, TextTestRunner, mock

## Developed and tested with
assert version_info >= (3,)



## Runtime
def Karlsruher(arguments):

	selftest = TestSuite()
	selftest.addTest(TestLoader().loadTestsFromTestCase(BotTest))

	if '-test' in arguments:
		logging.basicConfig(
			level = logging.DEBUG
			if '-debug' in arguments else logging.INFO,
			format = '[%(funcName)s]: %(message)s',
			handlers=[logging.StreamHandler()]
		)
		result = TextTestRunner(failfast=True).run(selftest)
	else:
		result = TestResult()
		selftest.run(result)

	selftestPassed=0==len(result.errors)==len(result.failures)

	if not '-test' in arguments:
		if not selftestPassed:
			print("Selftest failed, aborting.")
			print("Run again with -test -debug to see more")
			exit(1)

		logging.basicConfig(
			level = logging.DEBUG
			if '-debug' in arguments else logging.INFO,
			format = '%(asctime)s %(levelname)-5.5s [%(module)s#%(funcName)s]: %(message)s',
			handlers=[logging.StreamHandler()]
		)

		bot = Bot()
		bot.isReadonly = '-talk' not in arguments
		bot.doHouseKeeping = '-housekeeping' in arguments
		bot.run()
		exit(0)



## Bot class
class Bot:

	now = datetime.now()

	homeDirectory = path.dirname(path.realpath(__file__))

	isReadonly = True
	doHouseKeeping = False

	logger = None
	twitter = None
	botname = None
	db = None

	advisors = []
	followers = []


	def __init__(self, twitter = None):

		self.logger = logging.getLogger(__name__)

		if twitter:
			self.twitter = twitter

		else:
			credentials = self.homeDirectory + '/credentials.py'
			if not path.isfile(credentials):
				self.logger.error('Ooops, missing file: ' + credentials)
				self.logger.info('Please use the .example and your own API keys to create this file.')
				exit(1)

			from credentials import TWITTER_CONSUMER_KEY
			from credentials import TWITTER_CONSUMER_SECRET
			from credentials import TWITTER_ACCESS_KEY
			from credentials import TWITTER_ACCESS_SECRET

			oauth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
			oauth.set_access_token(TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET)

			self.twitter = tweepy.API(
				oauth,
				wait_on_rate_limit=True,
				wait_on_rate_limit_notify=True,
				compression=True
			)

		self.botname = self.twitter.me().screen_name
		self.logger.info('I am ' + self.botname + '.')
		self.initDatabase()
		self.initFollowers()
		self.initAdvisors()


	def sleepFile(self):
		return self.homeDirectory + '/.sleep.'+ self.botname.lower()

	def lockFile(self):
		return self.homeDirectory + '/.lock.'+ self.botname.lower()

	def lock(self, lockfile):
		if self.isLocked(lockfile):
			self.logger.info('Locked: ' + lockfile)
			exit(0)
		self.logger.debug('Locking "%s".', lockfile)
		open(lockfile, 'a').close()

	def unlock(self, lockfile):
		if self.isLocked(lockfile):
			self.logger.debug('Unlocking "%s".', lockfile)
			remove(lockfile)

	def isLocked(self, lockfile):
		return path.isfile(lockfile)


	def databaseFile(self):
		return self.homeDirectory + '/'+ self.botname.lower() + '.db'

	def initDatabase(self):
		database = self.databaseFile()
		self.logger.debug('Using file "%s" as database.', database)
		self.db = sqlite3.connect(database)
		self.db.row_factory = sqlite3.Row
		self.db.cursor().execute('CREATE TABLE IF NOT EXISTS tweets (tweetid PRIMARY KEY)')
		self.db.cursor().execute('CREATE TABLE IF NOT EXISTS followers (uid PRIMARY KEY, screen_name VARCHAR NOT NULL)')
		self.db.commit()

	def rememberTweet(self, tweet):
		self.logger.debug('Remembering tweet #%s', tweet.id)
		self.db.cursor().execute('INSERT OR IGNORE INTO tweets VALUES (?)', (str(tweet.id),))
		self.db.commit()

	def haveReadTweet(self, tweet):
		cursor = self.db.cursor()
		cursor.execute('SELECT tweetid FROM tweets WHERE tweetid = ?', (str(tweet.id),))
		return cursor.fetchone() != None




	def initAdvisors(self):
		self.advisors = []
		try:
			for user in self.twitter.list_members(self.botname, 'advisors'):
				self.advisors.append(str(user.screen_name))
		except Exception as e:
			self.logger.exception('Exception during API call.')
		self.logger.debug('I accept advice from %s', self.advisors)




	def initFollowers(self):
		self.followers = []
		select = self.db.cursor()
		select.execute('SELECT uid,screen_name FROM followers')
		for follower in select.fetchall():
			self.followers.append(str(follower['uid']))
		followerCount = len(self.followers)
		if(followerCount == 0):
			self.logger.info('I have NO followers, maybe testing or a problem?')
		self.logger.debug('I have %s followers.', followerCount)




	def reply(self, tweet, text):
		self.logger.debug('REPLYING: %s', text)
		if not self.isReadonly:
			try:
				self.twitter.update_status(
					status = text, in_reply_to_status_id = tweet.id
				)
			except Exception as e:
				self.logger.exception('Exception when replying.')

	def tweet(self, text):
		self.logger.debug('TWEETING: %s', text)
		if not self.isReadonly:
			try:
				self.twitter.update_status(status = text)
			except Exception as e:
				self.logger.exception('Exception when tweeting.')




	def houseKeeping(self):
		if not self.doHouseKeeping:
			return False

		self.lock(self.lockFile())
		self.logger.info('I am housekeeping.')
		startTime = datetime.now()
		try:
			self.fetchFollowersFromTwitter()
		except Exception as e:
			self.logger.exception('Exception during housekeeping.')
		self.logger.info('Housekeeping done, took: %s', datetime.now() - startTime)
		self.unlock(self.lockFile())
		return True




	def run(self):

		if self.houseKeeping():
			return


		self.lock(self.lockFile())
		self.logger.debug('I start a run now: ' + str(self.now))
		self.logger.info(
			'I am %s.',
			'READ ONLY' if self.isReadonly else 'T A L K I N G')
		startTime = datetime.now()
		for mention in self.twitter.mentions_timeline():
			self.readMention(mention)
		self.logger.info('Run took: %s, bye!', datetime.now() - startTime)
		self.unlock(self.lockFile())




	def readMention(self, mention):

		link = 'Read ' + str(mention.id)+ ' ' + str(mention.user.screen_name)

		if self.haveReadTweet(mention):
			self.logger.info('%s: read before.', link)
			return
		self.rememberTweet(mention)

		try:
			if self.adviceAction(mention):
				self.logger.info('%s: took advice.', link)
				return
			if self.retweetAction(mention):
				self.logger.info('%s: retweeted.', link)
				return
		except Exception as e:
			self.logger.exception('Exception with a mention.')

		self.logger.info('%s: ignored.', link)




	def adviceAction(self, tweet):

		if not tweet.user.screen_name in self.advisors:
			return False

		trigger = str('@' + self.botname + '!').lower()
		message = str(tweet.text)

		if not message.lower().startswith(trigger):
			return False

		advice = message[len(trigger):].strip().split()

		if not len(advice) == 2:
			return False

		action = advice[0].strip().lower()
		subject = advice[1].strip().lower()

		if subject in self.advisors:
			self.logger.info(
				'Ignoring advice: %s %s %s',
				tweet.user.screen_name, action, subject
			)
			return True

		self.logger.info(
			'Taking advice: %s %s %s',
			tweet.user.screen_name, action, subject
		)

		try:

			if action == 'geh' and subject == 'schlafen!':
				self.logger.debug('Sleeping %s.', subject)
				self.tweet('Automatische Nachricht: Ich retweete vorübergehend nicht mehr.')
				self.lock(self.sleepFile())
				return True

			if action == 'wach' and subject == 'auf!':
				self.logger.debug('Wache auf. %s.', subject)
				self.tweet('Automatische Nachricht: Ich retweete jetzt gleich wieder.')
				self.unlock(self.sleepFile())
				return True

			if action == '+mute':
				self.logger.debug('Muting %s.', subject)
				self.twitter.create_mute(screen_name = subject)
				self.reply(tweet, 'Danke, ich lese ' + subject + ' nicht mehr.')
				return True

			if action == '-mute':
				self.logger.debug('Unmuting %s.', subject)
				self.twitter.destroy_mute(screen_name = subject)
				self.reply(tweet, 'Danke, ich lese ' + subject + ' wieder.')
				return True

		except Exception as e:
			self.logger.exception('Exception when taking advice.')
			return True

		return False




	def retweetAction(self, mention):

		if self.isLocked(self.sleepFile()):
			self.logger.debug('I am sleeping.')
			return False

		if str(mention.user.screen_name) == self.botname:
			self.logger.debug('Not retweeting myself.')
			return False

		if str(mention.user.id) not in self.followers:
			self.logger.debug('%s not a follower, no retweet.', mention.user.screen_name)
			#self.reply(mention, 'Hallo, ich retweteete nur Follower.')
			return False

		if str(mention.user.protected) == 'True':
			self.logger.debug('%s is private user, no retweet.', mention.user.screen_name)
			#self.reply(mention, 'Hallo, ich retweete nur Follower mit öffentlichem Account.')
			return False

		if str(mention.in_reply_to_status_id_str) != 'None':
			self.logger.debug('%s wrote reply from hell, no retweet.', mention.user.screen_name)
			#self.reply(mention, 'Hallo, bitte halte mich aus dieser Unterhaltung heraus.')
			return False

		self.logger.debug('Retweeting %s @%s.', mention.id, mention.user.screen_name)

		if not self.isReadonly:
			try:
				self.twitter.retweet(mention.id)
			except Exception as e:
				self.logger.exception('Exception when retweeting.')

		return True




	def fetchFollowersFromTwitter(self):
		self.logger.warning('I am fetching my followers, this may take a while.')
		startTime = datetime.now()
		self.logger.debug('Deleting followers from DB.')
		self.db.cursor().execute('DELETE FROM followers')
		self.db.commit()
		self.logger.debug('Calling Twitter API and storing followers in DB.')
		self.twitter.followers.pagination_mode = 'cursor'
		for follower in tweepy.Cursor(self.twitter.followers).items():
			self.logger.debug('Adding %s.', follower.screen_name)
			self.db.cursor().execute('INSERT OR IGNORE INTO followers VALUES (?,?)', (str(follower.id),str(follower.screen_name)))
			self.db.commit()
		self.logger.info('Fetching followers done, took: %s', datetime.now() - startTime)
		self.initFollowers()




## TestCase
class BotTest(TestCase):

	bot = None

	def setUp(self):
		self.bot = Bot(
			mock.Mock(
				me = mock.MagicMock(
					return_value=mock.Mock(id = 8, screen_name='MockBot')
				),
				list_members = mock.MagicMock(
					return_value=[
						mock.Mock(id = 7, screen_name = 'advisor')
					]
				)
			)
		)
		self.bot.followers = ['1',]

	def tearDown(self):
		remove(self.bot.databaseFile())

	def test_bot_can_init(self):
		bot = self.bot
		self.assertEqual(bot.botname, 'MockBot')
		self.assertFalse(None in bot.advisors)
		self.assertFalse('' in bot.advisors)
		self.assertFalse('notadvisor' in bot.advisors)
		self.assertTrue('advisor' in bot.advisors)

	def test_bot_can_lock_and_unlock(self):
		bot = self.bot
		self.assertFalse(bot.isLocked(bot.lockFile()))
		bot.lock(bot.lockFile())
		self.assertTrue(bot.isLocked(bot.lockFile()))
		bot.unlock(bot.lockFile())
		self.assertFalse(bot.isLocked(bot.lockFile()))

	def test_bot_doesnot_take_advice_from_user(self):
		bot = self.bot
		self.assertFalse(
			bot.adviceAction(
				mock.Mock(
					id = 4711,
					text='foo bar',
					user=mock.Mock(id = 0, screen_name = 'user')
				)
			)
		)

	def test_bot_can_take_advice_from_advisor(self):
		bot = self.bot
		self.assertFalse(
			bot.adviceAction(
				mock.Mock(
					id = 4711,
					text='foo',
					user=mock.Mock(id = 7, screen_name = 'advisor')
				)
			)
		)

	def test_bot_can_protect_advisor(self):
		bot = self.bot
		self.assertTrue(
			bot.adviceAction(
				mock.Mock(
					id = 4711,
					text='@mockbot! +mute advisor',
					user=mock.Mock(id = 7, screen_name = 'advisor')
				)
			)
		)

	def test_bot_can_handle_advice_sleep(self):
		bot = self.bot
		self.assertTrue(
			bot.adviceAction(
				mock.Mock(
					id = 4711,
					text='@mockbot! gEh scHlafen!',
					user=mock.Mock(id = 7, screen_name = 'advisor')
				)
			)
		)
		self.assertTrue(bot.isLocked(bot.sleepFile()))
		bot.unlock(bot.sleepFile())

	def test_bot_can_handle_advice_wakeup(self):
		bot = self.bot
		self.assertTrue(
			bot.adviceAction(
				mock.Mock(
					id = 4711,
					text='@mockbot! wAch auf!',
					user=mock.Mock(id = 7, screen_name = 'advisor')
				)
			)
		)
		self.assertFalse(bot.isLocked(bot.sleepFile()))

	def test_bot_can_handle_advice_mute(self):
		bot = self.bot
		self.assertTrue(
			bot.adviceAction(
				mock.Mock(
					id = 4711,
					text='@mockbot! +mute user',
					user=mock.Mock(id = 7, screen_name = 'advisor')
				)
			)
		)

	def test_bot_can_handle_advice_unmute(self):
		bot = self.bot
		self.assertTrue(
			bot.adviceAction(
				mock.Mock(
					id = 4711,
					text='@mockbot! -mute user',
					user=mock.Mock(id = 7, screen_name = 'advisor')
				)
			)
		)

	def test_bot_doesnot_retweet_self(self):
		bot = self.bot
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					id = 4711,
					in_reply_to_status_id_str=None,
					text = 'Hey @MockBot, pls RT!',
					user = mock.Mock(id = 8, screen_name = self.bot.botname)
				)
			)
		)

	def test_bot_doesnot_retweet_nonfollower(self):
		bot = self.bot
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					id = 4711,
					in_reply_to_status_id_str = None,
					text = 'Hey @MockBot, pls RT!',
					user = mock.Mock(id = 5, screen_name = 'user')
				)
			)
		)

	def test_bot_doesnot_retweet_protected(self):
		bot = self.bot
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					id = 4711,
					in_reply_to_status_id_str = None,
					text = 'Hey @MockBot, pls RT!',
					user = mock.Mock(id = 3, screen_name = 'user', protected = True)
				)
			)
		)

	def test_bot_doesnot_retweet_reply(self):
		bot = self.bot
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					id = 4711,
					in_reply_to_status_id_str = '7500',
					text = 'Hey @MockBot, pls RT!',
					user = mock.Mock(id = 1, screen_name = 'follower')
				)
			)
		)

	def test_bot_can_retweet_follower(self):
		bot = self.bot
		self.assertTrue(
			bot.retweetAction(
				mock.Mock(
					id = 4711,
					in_reply_to_status_id_str=None,
					text = 'Hey @MockBot, pls RT!',
					user = mock.Mock(id = 1, screen_name = 'follower')
				)
			)
		)


	def test_bot_can_sleep(self):
		bot = self.bot
		self.assertFalse(bot.isLocked(bot.sleepFile()))
		bot.lock(bot.sleepFile())
		self.assertTrue(bot.isLocked(bot.sleepFile()))
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					id = 4711,
					in_reply_to_status_id_str=None,
					text = 'Hey @MockBot, pls RT!',
					user = mock.Mock(id = 1, screen_name = 'follower')
				)
			)
		)
		bot.unlock(bot.sleepFile())
		self.assertFalse(bot.isLocked(bot.sleepFile()))




## Main function and call
def main():
	Karlsruher(argv)
main()

## Feddich.
