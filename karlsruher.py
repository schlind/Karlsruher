#!/usr/bin/env python3
##
## Karlsruher Retweet Bot https://github.com/schlind/Karlsruher
## Cronjob:
##	*/5 *  * * * /path/to/karlsruher.py >> /path/to/karlsruher.log 2>&1
##

from datetime import datetime
from os import path, remove
from sys import version_info, argv, stdout, exit
from unittest import TestCase, TestSuite, TextTestRunner, mock
import sqlite3
import tweepy

import requests
import re

assert version_info >= (3,)

def Karlsruher(arguments):

	selftest = TestSuite()
	selftest.addTest(BotTest('test_bot_can_init'))
	selftest.addTest(BotTest('test_bot_doesnt_take_advice_from_user'))
	selftest.addTest(BotTest('test_bot_can_take_advice_from_advisor'))
	selftest.addTest(BotTest('test_bot_can_protect_advisor'))
	selftest.addTest(BotTest('test_bot_can_handle_advice_mute'))
	selftest.addTest(BotTest('test_bot_can_handle_advice_unmute'))
	selftest.addTest(BotTest('test_bot_doesnt_retweet_self'))
	selftest.addTest(BotTest('test_bot_doesnt_retweet_nonfollower'))
	selftest.addTest(BotTest('test_bot_doesnt_retweet_protected'))
	selftest.addTest(BotTest('test_bot_doesnt_retweet_reply'))
	selftest.addTest(BotTest('test_bot_can_retweet'))
	TextTestRunner().run(selftest)

	if not '-test' in arguments:
		bot = Bot()
		bot.readOnly = '-talk' not in arguments
		bot.run()


class Bot:

	readOnly = True
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


	def log(self, message, lineend='\n'):
		stdout.write(message + lineend)
		stdout.flush()


	def lockFile(self):
		return self.homedir + '/.lock.'+ self.botname.lower()


	def databaseFile(self):
		return self.homedir + '/'+ self.botname.lower() + '.db'


	def initDatabase(self):
		database = self.databaseFile()
		self.log('I am using file "' + database + '" as database.')
		self.db = sqlite3.connect(database)
		self.db.row_factory = sqlite3.Row
		self.db.cursor().execute('CREATE TABLE IF NOT EXISTS tweets (tweetid PRIMARY KEY)')
		self.db.cursor().execute('CREATE TABLE IF NOT EXISTS followers (uid PRIMARY KEY, screen_name VARCHAR NOT NULL)')
		self.db.commit()


	def rememberTweet(self, tweet):
		"""Remember that I read the given tweet."""
		self.db.cursor().execute('INSERT OR IGNORE INTO tweets VALUES (?)', (str(tweet.id),))
		self.db.commit()


	def haveReadTweet(self, tweet):
		"""Tell whether or not I already read the given tweet."""
		cursor = self.db.cursor()
		cursor.execute('SELECT tweetid FROM tweets WHERE tweetid = ?', (str(tweet.id),))
		return cursor.fetchone() != None


	def initAdvisor(self):
		"""Twitter API: list_members."""
		self.advisors = []
		try:
			for user in self.twitter.list_members(self.botname, 'advisor'):
				self.advisors.append(str(user.screen_name))
		except Exception as e:
			# Expected from any API call.
			self.log('Exception: ' + str(e))

		self.log('I accept advice from ' + str(self.advisors))


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


	def readMention(self, mention):

		self.log('+ Reading https://twitter.com/' + mention.user.screen_name + '/status/' + str(mention.id))

		if self.haveReadTweet(mention):
			self.log('-> Tweet was read before, no action.')
			return

		self.rememberTweet(mention)

		try:
			if self.adviceAction(mention):
				return
			self.retweetAction(mention)

		except Exception as e:
			self.log('Exception: ' + str(e))


	def reply(self, tweet, text):

		self.log('REPLYING: ' + text)

		if self.readOnly == True:
			return True

		try:
			self.twitter.update_status(
				status = text, in_reply_to_status_id = tweet.id
			)
		except Exception as e:
			self.log('Exception: ' + str(e))


	def tweet(self, text):

		self.log('TWEETING: ' + text)

		if self.readOnly == True:
			return True

		try:
			self.twitter.update_status(status = text)
		except Exception as e:
			self.log('Exception: ' + str(e))




	def adviceAction(self, tweet):

		if not tweet.user.screen_name in self.advisors:
			return False

		self.log('- adviceAction:', ' ')

		trigger = str('@' + self.botname + '!').lower()
		message = str(tweet.text)

		if message.lower().startswith(trigger):

			advice = message[len(trigger):].strip().split()

			if len(advice) == 2:

				action = advice[0].strip().lower()
				subject = advice[1].strip()

				if subject in self.advisors:
					self.log('ignoring ' + action + ' ' + subject)
					return True

				self.log(action + ' ' + subject)

				try:

					if action == '+mute':
						self.twitter.create_mute(screen_name = subject)
						self.reply(tweet, 'Danke, ich lese ' + subject + ' nicht mehr.')
						return True

					if action == '-mute':
						self.twitter.destroy_mute(screen_name = subject)
						self.reply(tweet, 'Danke, ich lese ' + subject + ' wieder.')
						return True

				except Exception as e:
					self.log('Exception: ' + str(e))
					return True

		return False




	def retweetAction(self, mention):

		self.log('- retweetAction:', ' ')

		if str(mention.user.screen_name) == self.botname:
			self.log('myself, oops, no retweet.')
			return False

		if mention.user.id not in self.followers:
			self.log('not a follower, no retweet.')
			#self.reply(mention, 'Hallo, ich retweteete nur Follower.')
			return False

		if str(mention.user.protected) == 'True':
			self.log('private user, no retweet.')
			#self.reply(mention, 'Hallo, ich retweete nur Follower mit öffentlichem Account.')
			return False

		if str(mention.in_reply_to_status_id_str) != 'None':
			self.log('reply from hell, no retweet.')
			#self.reply(mention, 'Hallo, bitte halte mich aus dieser Unterhaltung heraus.')
			return False

		self.log('RETWEETING.')

		if self.readOnly == True:
			return True

		try:
			self.twitter.retweet(tweet.id)
			return True
		except Exception as e:
			self.log('Exception: ' + str(e))

		return False




	def houseKeeping(self):

		if self.timenow.hour == 1 and self.timenow.minute <= 5:
			self.log('I am fetching my followers, this may take a while.', '')

			self.db.cursor().execute('DELETE FROM followers')
			self.db.commit()

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








class BotTest(TestCase):

	bot = None

	def setUp(self):
		self.bot = Bot(
			mock.Mock(
				me = mock.MagicMock(
					return_value=mock.Mock(id = 8, screen_name='MockBot')),
					list_members = mock.MagicMock(
						return_value=[
							mock.Mock(id = 7, screen_name = 'advisor')
						]
					)
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
		self.assertTrue('advisor' in bot.advisors)

	def test_bot_doesnt_take_advice_from_user(self):
		bot = self.bot
		self.assertFalse(
			bot.adviceAction(
				mock.Mock(
					text='foo',
					user=mock.Mock(id = 0, screen_name = 'user')
				)
			)
		)

	def test_bot_can_take_advice_from_advisor(self):
		bot = self.bot
		self.assertFalse(
			bot.adviceAction(
				mock.Mock(
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
					text='@mockbot! +mute advisor',
					user=mock.Mock(id = 7, screen_name = 'advisor')
				)
			)
		)

	def test_bot_can_handle_advice_mute(self):
		bot = self.bot
		self.assertTrue(
			bot.adviceAction(
				mock.Mock(
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
					text='@mockbot! -mute user',user=mock.Mock(id = 7, screen_name = 'advisor')
				)
			)
		)

	def test_bot_doesnt_retweet_self(self):
		bot = self.bot
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					user = mock.Mock(id = 8, screen_name = self.bot.botname),
					in_reply_to_status_id_str=None,
					text = 'Hey @MockBot, pls RT!'
				)
			)
		)

	def test_bot_doesnt_retweet_nonfollower(self):
		bot = self.bot
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					user = mock.Mock(id = 5, screen_name = 'user'),
					in_reply_to_status_id_str=None,
					text = 'Hey @MockBot, pls RT!'
				)
			)
		)

	def test_bot_doesnt_retweet_protected(self):
		bot = self.bot
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					user = mock.Mock(id = 3, screen_name = 'user', protected = True),
					in_reply_to_status_id_str=None,
					text = 'Hey @MockBot, pls RT!'
				)
			)
		)

	def test_bot_doesnt_retweet_reply(self):
		bot = self.bot
		bot.followers = [1,]
		self.assertFalse(
			bot.retweetAction(
				mock.Mock(
					user = mock.Mock(id = 1, screen_name = 'follower'),
					in_reply_to_status_id_str='4711',
					text = 'Hey @MockBot, pls RT!'
				)
			)
		)

	def test_bot_can_retweet(self):
		bot = self.bot
		bot.followers = [1,]
		self.assertTrue(
			bot.retweetAction(
				mock.Mock(
					user = mock.Mock(id = 1, screen_name = 'follower'),
					in_reply_to_status_id_str=None,
					text = 'Hey @MockBot, pls RT!'
				)
			)
		)




Karlsruher(argv)
