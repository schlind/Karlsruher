#!/usr/bin/env python

## quick & dirty mock for tweepy

class mock:
	"""Simple object, there might be a more simple approach, but I didn't care."""
	pass

class twitter:
	"""Provide definitions from the tweepy Twitter API adapter"""

	def me(self):
		u = mock()
		u.screen_name = "MockBot"
		u.protected = False
		return u

	def __mockATweet(self, tweetid, in_reply_to_status_id_str, screen_name, protected,text=None):
		mockTweet = mock()
		mockTweet.id = tweetid
		mockTweet.in_reply_to_status_id_str = in_reply_to_status_id_str
		mockTweet.user = mock()
		mockTweet.user.screen_name = screen_name
		mockTweet.user.protected = protected
		mockTweet.text = text
		return mockTweet

	def mentions_timeline(self):
		return [
			## Feature "advise"
			self.__mockATweet(101,None,'schlind',False,'@MoCkBot! Das ist kein Kommando.'),
			self.__mockATweet(102,None,'schlind',False,'@MockBot! ping'),
			self.__mockATweet(103,None,'schlind',False,'@MockBot!mute Laberbacke '),
			self.__mockATweet(104,None,'schlind',False,'@MockBot! unmute Laberbacke '),
			self.__mockATweet(100,None,'nobody',False,'@MockBot! ping'),
			## Feature "retweet"
			self.__mockATweet(1000001,None,'public_user',False),
			self.__mockATweet(1000002,None,'public_user',False,'@mockbot! Retweete mich!'),
			self.__mockATweet(2000001,None,'private_user',True),
			self.__mockATweet(3000001,'4711','reply_user',False),
		]


	def update_status(self,x,y=None):
		pass
	def retweet(self,x):
		pass
	def create_mute(self, screen_name):
		pass
	def destroy_mute(self, screen_name):
		pass
