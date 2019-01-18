#!/usr/bin/env python3


from datetime import datetime
from os import path, remove
from sys import version_info, argv, stdout, exit
assert version_info >= (3, 7)
from unittest import TestCase, TestSuite, TextTestRunner, mock
import sqlite3
import tweepy


def Karlsruher(arguments):
	suite = TestSuite()
	suite.addTest(BotTest('test_bot_can_init'))
	suite.addTest(BotTest('test_bot_can_handle_lockfile'))
	suite.addTest(BotTest('test_bot_can_handle_advise'))
	suite.addTest(BotTest('test_bot_can_retweet'))
	TextTestRunner().run(suite)
	if not '-test' in arguments:
		bot = Bot()
		bot.readOnly = '-talk' not in arguments
		bot.run()


class Bot:

	readOnly=True
	homedir = path.dirname(path.realpath(__file__))
	timenow = datetime.now()
	twitter = None
	botname = None
	db = None
	advisors = []
	followers = []


	def __init__(self, twitter = None):

		if twitter:
			self.twitter = twitter

		else:
			credentials = self.homedir + '/credentials.py'
			if not path.isfile(credentials):
				self.log('Ooops, missing file: ' + credentials)
				self.log('Please use the .example and your own API keys to create this file.')
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
		self.log('I am ' + self.botname + '.')
		self.initAdvisor()
		self.initDatabase()


	def __del__(self):
		pass


	def log(self, message, lineend='\n'):
		"""May use a framework later, lol."""
		stdout.write(message + lineend)
		stdout.flush()

	def lockFile(self):
		return self.homedir + '/.lock.'+ self.botname

	def databaseFile(self):
		return self.homedir + '/'+ self.botname + '.db'

	def initDatabase(self):
		database = self.databaseFile()
		self.log('I am using file "' + database + '" as database.')
		self.db = sqlite3.connect(database)
		self.db.row_factory = sqlite3.Row
		self.db.cursor().execute('CREATE TABLE IF NOT EXISTS tweets (tweetid PRIMARY KEY)')
		self.db.cursor().execute('CREATE TABLE IF NOT EXISTS followers (uid PRIMARY KEY, screen_name VARCHAR NOT NULL)')
		self.db.commit()

	def initAdvisor(self):
		"""Twitter API: list_members."""
		self.advisors = []
		try:
			for user in self.twitter.list_members(self.botname, 'advisor'):
				self.advisors.append(str(user.screen_name))
		except Exception as e:
			# Expected from any API call.
			self.log('Exception: ' + str(e))

		self.log('I accept advise from ' + str(self.advisors))


	def run(self):
		self.log('I start a run now: ' + str(self.timenow))
		if self.readOnly == True:
			self.log('I am READ ONLY, not talking to twitter this time.')
		else:
			self.log('I am TALKING to twitter this time.')

		lockfile = self.lockFile()
		if path.isfile(lockfile):
			self.log('Aborting, lock file present: ' + lockfile)
			exit(0)
		open(lockfile, 'a').close()

		self.houseKeeping()

		# https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-mentions_timeline
		for mention in self.twitter.mentions_timeline():
			self.readMention(mention)
		self.log('Read all mentions.')

		if path.isfile(lockfile):
			remove(lockfile)
		self.log('Bye.')


	def rememberTweet(self, tweet):
		"""Remember that I read the given tweet."""
		self.db.cursor().execute('INSERT OR IGNORE INTO tweets VALUES (?)', (str(tweet.id),))
		self.db.commit()


	def haveReadTweet(self, tweet):
		"""Tell whether or not I already read the given tweet."""
		cursor = self.db.cursor()
		cursor.execute('SELECT tweetid FROM tweets WHERE tweetid = ?', (str(tweet.id),))
		return cursor.fetchone() != None


	def readMention(self, mention):

		self.log('+ Reading https://twitter.com/' + mention.user.screen_name + '/status/' + str(mention.id))

		if self.haveReadTweet(mention):
			self.log('-> Tweet was read before, no action.')
			return

		self.rememberTweet(mention)

		try:
			if self.adviseAction(mention):
				return
			self.retweetAction(mention)

		except Exception as e:
			self.log('Exception: ' + str(e))






	def adviseAction(self, tweet):

		if not tweet.user.screen_name in self.advisors:
			return False

		trigger = str('@' + self.botname + '!').lower()
		message = str(tweet.text)

		if message.lower().startswith(trigger):

			advise = message[len(trigger):].strip().split()

			if len(advise) == 2:

				action = advise[0].strip().lower()
				subject = advise[1].strip()

				if subject in self.advisors:
					self.log('ignoring: ' + action + ' @' + subject)
					return True

				self.log(action + ' @' + subject)

				try:

					if action == 'sleep':
						self.log("" + int(subject))
						self.reply(tweet, 'Danke, ich lege mich schlafen.')
						return True

					if action == 'mute':
						self.twitter.create_mute(screen_name = subject)
						self.reply(tweet, 'Danke, ich lese ' + subject + ' nicht mehr.')
						return True

					if action == 'unmute':
						self.twitter.destroy_mute(screen_name = subject)
						self.reply(tweet, 'Danke, ich lese ' + subject + ' wieder.')
						return True

				except Exception as e:
					self.log("Exception: " + str(e))
					return True

		return False


	def retweetAction(self, mention):

		self.log('retweetAction:', ' ')

		if str(mention.user.screen_name) == self.botname:
			self.log('myself, oops, no retweet.')
			return False

		if str(mention.user.id) not in self.followers:
			self.log('not a follower, no retweet.')
			self.reply(mention, 'Hallo, ich retweteete nur Follower.')
			return False

		if str(mention.user.protected) == 'True':
			self.log('private user, no retweet.')
			self.reply(mention, 'Hallo, ich retweete nur Follower mit öffentlichem Account.')
			return False

		if str(mention.in_reply_to_status_id_str) and str(mention.in_reply_to_status_id_str) != 'None':
			self.log('reply from hell, no retweet.')
			self.reply(mention, 'Hallo, bitte halte mich aus dieser Unterhaltung heraus.')
			return False

		self.log('RETWEETING.')

		if self.readOnly == True:
			return True

		try:
			self.twitter.retweet(tweet.id)
		except Exception as e:
			self.log("Exception: " + str(e))

		return False


	def reply(self, tweet, message):
		self.log('REPLYING: ' + message)
		if self.readOnly == True:
			return True
		try:
			self.twitter.update_status(
				status = message, in_reply_to_status_id = tweet.id
			)
		except Exception as e:
			self.log("Exception: " + str(e))













	def houseKeeping(self):
		"""Let me take care of things that are not triggered by tweets."""

#		if self.timenow.hour == 1 and self.timenow.minute <= 5:
		self.log('I am fetching my followers, this may take a while.', '')
		self.twitter.followers.pagination_mode='cursor'
		for follower in tweepy.Cursor(self.twitter.followers).items():
			self.log('+','')
			self.db.cursor().execute('INSERT OR IGNORE INTO followers VALUES (?,?)', (str(follower.id),str(follower.screen_name)))
			self.db.commit()
		self.log('done.')


		self.followers = []
		select = self.db.cursor()
		select.execute('SELECT uid,screen_name FROM followers')
		for follower in select.fetchall():
			self.followers.append(follower['uid'])

		self.log('I have ' + str(len(self.followers)) + ' followers.')
		return




class BotTest(TestCase):

	apiMock = None

	bot = None

	def setUp(self):
		self.bot = Bot(
			mock.Mock(
				me = mock.MagicMock(return_value=mock.Mock(screen_name='MockBot')),
				list_members = mock.MagicMock(return_value=[
					mock.Mock(screen_name = 'advisor1'),
					mock.Mock(screen_name = 'advisor2')
				])
			)
		)

	def tearDown(self):
		remove(self.bot.databaseFile())
		pass

	def test_bot_can_init(self):
		bot = self.bot
		self.assertEqual(bot.botname, 'MockBot')
		self.assertFalse(None in bot.advisors)
		self.assertFalse('' in bot.advisors)
		self.assertFalse('notadvisor' in bot.advisors)
		self.assertTrue('advisor1' in bot.advisors)
		self.assertTrue('advisor2' in bot.advisors)

	def test_bot_can_handle_lockfile(self):
		bot = self.bot
		open(bot.lockFile(), 'a').close()
		self.assertTrue(path.isfile(bot.lockFile()))
		remove(bot.lockFile())
		self.assertFalse(path.isfile(bot.lockFile()))

	def test_bot_can_handle_advise(self):
		bot = self.bot
		user = mock.Mock(screen_name = 'user')
		advisor = mock.Mock(screen_name = 'advisor1')
		self.assertFalse(bot.adviseAction(mock.Mock(text='foo',user=user)))
		self.assertFalse(bot.adviseAction(mock.Mock(text='foo',user=advisor)))
		self.assertTrue(bot.adviseAction(mock.Mock(text='@mockbot! mute xxx',user=advisor)))
		self.assertTrue(bot.adviseAction(mock.Mock(text='@mockbot! unmute xxx',user=advisor)))
		self.assertTrue(bot.adviseAction(mock.Mock(text='@mockbot! mute advisor2',user=advisor)))
		self.assertFalse(bot.adviseAction(mock.Mock(text='@mockbot! mute xxx',user=user)))

	def test_bot_can_retweet(self):

		bot = self.bot

		realCursor = tweepy.Cursor.items
		tweepy.Cursor.items = mock.MagicMock(return_value=[
			mock.Mock(id=1, screen_name = 'follower1'),
			mock.Mock(id=2, screen_name = 'follower2')
		])
		bot.houseKeeping()
		tweepy.Cursor.items = realCursor

		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					in_reply_to_status_id_str=None,
					text='@MockBot, pls RT',
					user = mock.Mock(id = 0, screen_name = 'user')
				)
			)
		)
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					in_reply_to_status_id_str=None,
					text='@MockBot, pls RT',
					user = mock.Mock(id = 0, screen_name = 'user')
				)
			)
		)
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					in_reply_to_status_id_str=None,
					text='@MockBot, pls RT',
					user = mock.Mock(id = 1, screen_name = 'follower1', protected = True)
				)
			)
		)
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					in_reply_to_status_id_str='4711',
					text='@MockBot, pls RT',
					user = mock.Mock(id = 1, screen_name = 'follower1')
				)
			)
		)
		self.assertTrue(
			bot.retweetAction(
				mock.Mock(
					in_reply_to_status_id_str=None,
					text='@MockBot, pls RT',
					user = mock.Mock(id = 1, screen_name = 'follower1')
				)
			)
		)


Karlsruher(argv)
