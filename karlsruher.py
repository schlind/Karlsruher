#!/usr/bin/env python

import sys
import sqlite3

class Bot:

	botname = None
	twitter = None
	sqlite3 = None

	def __init__(self, twitter):

		self.twitter = twitter
		self.botname = twitter.me().screen_name

		self.sqlite3 = sqlite3.connect( self.botname + '.db')
		self.sqlite3.cursor().execute('CREATE TABLE IF NOT EXISTS retweets (tweetid PRIMARY KEY)')
		#self.sqlite3.cursor().execute('CREATE TABLE IF NOT EXISTS mute (screen_name PRIMARY KEY)')

		self.sqlite3.commit()


	def log(self, message, lineend='\n'):
		sys.stdout.write(message + lineend)
		sys.stdout.flush()


	def __rememberTweet(self, tweet):
		self.sqlite3.cursor().execute('INSERT OR IGNORE INTO retweets VALUES (?)', (str(tweet.id),))
		self.sqlite3.commit()


	def __haveRetweeted(self, tweet):
		cursor = self.sqlite3.cursor()
		cursor.execute('SELECT tweetid FROM retweets WHERE tweetid = ?', (str(tweet.id),))
		return cursor.fetchone() != None


	def readMentions(self):

		self.log('Reading mentions for ' + self.botname)

		for mention in self.twitter.mentions_timeline():

			self.log('Reading https://twitter.com/' + str(mention.user.screen_name) + '/status/' + str(mention.id) + ' -> ', '' )

			if str(mention.user.screen_name) == self.botname:
				self.log('is by myself, oops.')
				continue

			if self.__haveRetweeted(mention):
				self.log('read before.')
				continue

			self.__rememberTweet(mention)

			if str(mention.user.protected) == 'True':
				self.log('is private.')
				message = 'Hallo, ich retweete keine privaten Nutzer.'
				self.twitter.update_status('@' + mention.user.screen_name + ' ' + message, mention.id)
				continue

			self.log('retweeting!')
			self.twitter.retweet(mention.id)

		self.sqlite3.close()
		self.log('Read all mentions, bye.' )
