#!/usr/bin/env python

## quick & dirty mock for tweepy

class mock:
	pass

class twitter:

	def me(self):

		u = mock()
		u.screen_name = "MockBot"
		u.protected = False

		return u


	def mentions_timeline(self):

		pUser = mock()
		pUser.screen_name = "_PROTECTED"
		pUser.protected = True

		pTweet = mock()
		pTweet.id = 4711
		pTweet.user = pUser
		pTweet.in_reply_to_status_id_str = ''

		u = mock()
		u.screen_name = "Laberbacke"
		u.protected = False

		t = mock()
		t.id = 1234
		t.user = u
		t.in_reply_to_status_id_str = 'Banane'

		return [ pTweet, t ]


	def update_status(self,x,y=None):
		pass


	def retweet(self,x):
		pass
