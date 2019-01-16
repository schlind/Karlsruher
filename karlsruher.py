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

		databaseFile = path.dirname(path.realpath(__file__)) + '/' + self.botname.lower() + '.db'
		self.__log('I am using file "' + databaseFile + '" as database.')
		self.sqlite3 = sqlite3.connect(databaseFile)
		self.sqlite3.cursor().execute('CREATE TABLE IF NOT EXISTS retweets (tweetid PRIMARY KEY)')
		self.sqlite3.commit()


	def __del__(self):
		"""Let me close resources."""
		self.sqlite3.close()
		self.__log('Bye.' )




	def heartBeat(self, readonly=True):
		"""
		Give me a heartbeat from time to time!
		I'm not looking for work unless being heartly beaten.
		"""
		self.__log('I received a heartbeat, will look for work now...')
		self.ismuted = readonly
		if self.ismuted:
			self.__log('I am MUTED, not talking to twitter this time.')
		self.__houseKeeping()
		self.__readMentions()




	def __readMentions(self):
		"""
		Let me read my latest mentions and delegate further action.
		https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-mentions_timeline
		"""
		for mention in self.twitter.mentions_timeline():

			self.__log('+ Reading https://twitter.com/' + str(mention.user.screen_name) + '/status/' + str(mention.id))

			if self.__actOnAdvise(mention):
				continue

			self.__retweetAction(mention)

		self.__log('Read all mentions.' )


	def __houseKeeping(self):
		"""Let me take care of things that are not triggered by tweets."""
		self.__log('I do not have any housekeeping to do.')
		return


	def __log(self, message, lineend='\n'):
		"""May use a framework later, lol."""
		stdout.write(message + lineend)
		stdout.flush()


	def __tweet(self, message):
		"""Let me send a Tweet."""
		self.__log('-> TWEET "' + message + '"')
		if not self.ismuted:
			try:
				self.twitter.update_status(message)
			except TweepError as e:
				self.__log("TweepError, I don't care: " + str(e))


	def __reply(self, tweet, message):
		"""Let me reply to the given Tweet."""
		self.__log('-> TWEET "' + message + '" (to tweetid ' + str(tweet.id) +')')
		if not self.ismuted:
			try:
				self.twitter.update_status(message, tweet.id)
			except TweepError as e:
				self.__log("TweepError, I don't care: " + str(e))




	def __actOnAdvise(self, tweet):
		"""
		I will act on advise and return True if there was any action.
		"""
		self.__log('-> Checking for advise', '...')

		if not self.__isAdvisor(tweet.user):
			self.__log(tweet.user.screen_name + ' is not my advisor.')
			return False

		trigger = str('@' + self.botname + '!').lower()
		message = tweet.text

		if message.lower().startswith(trigger):

			advise = message[len(trigger):].strip().split()

			if len(advise) == 2:

				action = advise[0].strip()
				victim = advise[1].strip()

				self.__log('action ' + action + ' @' + victim)

				try:

					if action == 'mute':
						self.twitter.create_mute(screen_name = victim)
						return True

					if action == 'unmute':
						self.twitter.destroy_mute(screen_name = victim)
						return True

				except TweepError as e:
					self.__log("TweepError, I don't care: " + str(e))


		return False


	def __isAdvisor(self, user):
		"""Indicate whether or not the specified user is an advisor to me.

		TODO This has to be a group of people, maybe a list in DB or at
		twitter.
		"""
		return user.screen_name.lower() == 'schlind'




	def __retweetAction(self, mention):
		"""
		Maybe retweet.

		I will NOT retweet mentions, which:
		* are tweeted by myself, uh.
		* are a reply from hell.
		* are by private users (applied DSGVO).
		* were read/retweeted by me before.
		"""
		self.__log('-> Checking for retweet', '...')

		if str(mention.user.screen_name) == self.botname:
			self.__log('is by myself, oops, no retweet.')
			return

		if str(mention.in_reply_to_status_id_str) and str(mention.in_reply_to_status_id_str) != 'None':
			self.__log('is a reply from hell, no retweet.')
			return

		if str(mention.user.protected) == 'True':
			self.__log('is private, no retweet.')
			return

		if self.__haveRetweeted(mention):
			self.__log('was read before, no retweet.')
			return

		self.__log('retweeting!')
		self.__rememberRetweet(mention)
		if not self.ismuted:
			try:
				self.twitter.retweet(tweet.id)
			except TweepError as e:
				self.__log("TweepError, I don't care: " + str(e))



	def __rememberRetweet(self, tweet):
		"""Remember that I retweeted the given tweet."""
		self.sqlite3.cursor().execute('INSERT OR IGNORE INTO retweets VALUES (?)', (str(tweet.id),))
		self.sqlite3.commit()


	def __haveRetweeted(self, tweet):
		"""Tell whether or not I already retweeted the given tweet."""
		cursor = self.sqlite3.cursor()
		cursor.execute('SELECT tweetid FROM retweets WHERE tweetid = ?', (str(tweet.id),))
		return cursor.fetchone() != None
