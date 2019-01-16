#!/usr/bin/env python

import sqlite3
from datetime import datetime
from os import path
from sys import stdout

class Bot:

	"""
	Hello, I am a Twitter Bot and I want to help.
	Therefore I read my timelines and behave well.
	"""


	ismuted = True
	timenow = str(datetime.now())
	botname = 'will be taken from my Twitter account'
	twitter = None
	sqlite3 = None
	advisor = []




	def __init__(self, twitter):
		"""
		Wake me up!

		I need at least a twitter client and expect something like
		the "tweepy" Twitter API adapter thingy to read from and
		write to Twitter.

		I am muted (reading and acting real internally, but without
		writing to Twitter) by default. If you want me to really talk,
		give readonly=False.

		Read, understand, act. Once you've got me as an object, just
		call the heartBeat definition.
		"""
		self.twitter = twitter
		self.botname = twitter.me().screen_name
		self.__log(self.timenow + ' Hello, I am ' + self.botname + '.')
		self.__initDatabase(path.dirname(path.realpath(__file__)) + '/' + self.botname.lower() + '.db')
		self.__readAdvisorMembers()


	def __del__(self):
		"""
		Let me sleep.
		"""
		self.sqlite3.close()
		self.__log('Bye.')


	def __initDatabase(self, database):
		"""
		Let me have a brain.
		"""
		self.__log('I am using file "' + database + '" as brain.')
		self.sqlite3 = sqlite3.connect(database)
		self.sqlite3.cursor().execute('CREATE TABLE IF NOT EXISTS tweets (tweetid PRIMARY KEY)')
		self.sqlite3.commit()


	def __rememberTweet(self, tweet):
		"""Remember that I read the given tweet."""
		self.sqlite3.cursor().execute('INSERT OR IGNORE INTO tweets VALUES (?)', (str(tweet.id),))
		self.sqlite3.commit()


	def __haveReadTweet(self, tweet):
		"""Tell whether or not I already read the given tweet."""
		cursor = self.sqlite3.cursor()
		cursor.execute('SELECT tweetid FROM tweets WHERE tweetid = ?', (str(tweet.id),))
		return cursor.fetchone() != None


	def __houseKeeping(self):
		"""Let me take care of things that are not triggered by tweets."""
		self.__log('I do not have any housekeeping to do.')
		return


	def __log(self, message, lineend='\n'):
		"""May use a framework later, lol."""
		stdout.write(message + lineend)
		stdout.flush()


	def __retweet(self, tweet):
		"""
		Let me retweet a Tweet.
		"""
		self.__log('-> RETWEET ' + str(tweet.id))
		if not self.ismuted:
			try:
				self.twitter.retweet(tweet.id)
			except Exception as e:
				# expect errors when retweeting a tweet twice
				self.__log("Exception, I don't care: " + str(e))


	def __tweet(self, message):
		"""
		Let me send a Tweet.
		"""
		self.__log('-> TWEET "' + message + '"')
		if not self.ismuted:
			try:
				self.twitter.update_status(message)
			except Exception as e:
				self.__log("Exception, I don't care: " + str(e))


	def __reply(self, tweet, message):
		"""
		Let me reply to a Tweet.
		"""
		self.__log('-> TWEET "' + message + '" (to tweetid ' + str(tweet.id) +')')
		if not self.ismuted:
			try:
				self.twitter.update_status(message, tweet.id)
			except Exception as e:
				self.__log("Exception, I don't care: " + str(e))


	def __readMentions(self):
		"""
		Let me read my latest mentions and delegate further action.
		https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-mentions_timeline
		"""
		for mention in self.twitter.mentions_timeline():
			self.__readMention(mention)
		self.__log('Read all mentions.' )


	def __readMention(self, mention):
		"""
		Let me read a single mention.
		"""
		self.__log('+ Reading https://twitter.com/' + mention.user.screen_name + '/status/' + str(mention.id))

		if self.__haveReadTweet(mention):
			self.__log('-> Tweet was read before, no action.')
			return

		self.__rememberTweet(mention)

		try:
			if self.__adviseAction(mention):
				return
			self.__retweetAction(mention)
		except Exception as e:
			self.__log('Exception: ' + str(e))




	def __adviseAction(self, tweet):
		"""
		I will act on advise and return True if there was any action.
		"""
		if not self.__isAdvisor(tweet.user.screen_name):
			return False

		self.__log('-> Checking for advise from ' + tweet.user.screen_name , '... ')

		trigger = str('@' + self.botname + '!').lower()
		message = tweet.text

		if message.lower().startswith(trigger):

			advise = message[len(trigger):].strip().split()

			if len(advise) == 2:

				action = advise[0].strip()
				victim = advise[1].strip()

				self.__log(action + ' @' + victim)

				try:

					if action == 'mute':
						self.twitter.create_mute(screen_name = victim)
						return True

					if action == 'unmute':
						self.twitter.destroy_mute(screen_name = victim)
						return True

				except Exception as e:
					# expect errors when muting muted and unmuting unmuted users
					self.__log("Exception, I don't care: " + str(e))
					return True

		self.__log('no action.')

		return False


	def __isAdvisor(self, user_screen_name):
		"""
		Indicate whether or not the specified user is an advisor to me.
		"""
		removeme = user_screen_name == 'schlind'
		if removeme or user_screen_name in self.advisor:
			return True

		return False


	def __readAdvisorMembers(self):
		"""
		Let me read the members of the advisor list.
		"""
		try:
			for user in self.twitter.list_members(self.botname, 'advisor'):
				self.advisor.append(str(user.screen_name))
		except Exception as e:
			self.__log('Exception: ' + str(e))

		self.__log('I accept advise from ' + str(self.advisor))




	def __retweetAction(self, mention):
		"""
		Maybe retweet.

		I will NOT retweet mentions, which:
		* are tweeted by myself, uh.
		* are a reply from hell.
		* are by private users (applied DSGVO).
		* were read/retweeted by me before.
		"""

		self.__log('-> Checking for retweet', '... ')

		if str(mention.user.screen_name) == self.botname:
			self.__log('is by myself, oops, no retweet.')
			return

		if str(mention.in_reply_to_status_id_str) and str(mention.in_reply_to_status_id_str) != 'None':
			self.__log('is a reply from hell, no retweet.')
			return

		if str(mention.user.protected) == 'True':
			self.__log('is private, no retweet.')
			return

		self.__retweet(mention)




	def heartBeat(self, readonly=True):
		"""
		Give me a heartbeat from time to time!
		I'm not looking for work unless being heartly beaten.
		"""
		self.__log('I received a heartbeat, will look for tweets now...')

		self.ismuted = readonly
		if self.ismuted:
			self.__log('I am MUTED, not talking to twitter this time.')

		self.__houseKeeping()
		self.__readMentions()
