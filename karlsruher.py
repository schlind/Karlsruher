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

		self.log('I am ' + self.botname)

		self.sqlite3 = sqlite3.connect( self.botname + '.db')
		self.sqlite3.cursor().execute('CREATE TABLE IF NOT EXISTS retweets (tweetid PRIMARY KEY)')
		self.sqlite3.cursor().execute('CREATE TABLE IF NOT EXISTS muted (screen_name PRIMARY KEY, timeout INTEGER NOT NULL)')

		self.sqlite3.commit()


	def __del__(self):
		self.sqlite3.close()
		self.log('Bye.' )


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

		## See https://developer.twitter.com/en/docs/tweets/timelines/api-reference/get-statuses-mentions_timeline

		for mention in self.twitter.mentions_timeline():

			self.log('Reading https://twitter.com/' + str(mention.user.screen_name) + '/status/' + str(mention.id) + ' -> ', '' )

			if str(mention.user.screen_name) == self.botname:
				self.log('is by myself, oops.')
				continue

			if str(mention.in_reply_to_status_id_str) and str(mention.in_reply_to_status_id_str) != 'None':
				self.log('is a reply from hell.')
				continue

			if str(mention.user.protected) == 'True':
				self.log('is private.')
				continue

			if self.__haveRetweeted(mention):
				self.log('read before.')
				continue

			self.log('retweeting!')

			self.__rememberTweet(mention)
			self.twitter.retweet(mention.id)

		self.log('Read all mentions.' )
