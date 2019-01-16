#!/usr/bin/env python
##
## Laufzeitumgebung fuer den Karlsruher Retweet Bot
##
## crontab -e:
## */5 * * * * /path/to/karlsruher/run-cron.sh >/dev/null 2>&1
##

import karlsruher
from os import path
from sys import argv, exit

USE_MOCK=False
READ_ONLY=True
for arg in argv:
	if arg == "-test":
		USE_MOCK = True
	if arg == "-talk":
		READ_ONLY = False

if USE_MOCK:
	import mock
	twitter = mock.twitter()

else:

	credentials = path.dirname(path.realpath(__file__)) + '/credentials.py'

	if not path.isfile(credentials):
		print 'Ooops, missing file: ' + credentials
		print 'Please use the .example and your own API keys to create this file.'
		exit(1)

	execfile(credentials)

	import tweepy
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
	twitter = tweepy.API(auth)


karlsruher.Bot(twitter).heartBeat(READ_ONLY)
