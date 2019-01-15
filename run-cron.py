#!/usr/bin/env python
##
## Laufzeitumgebung fuer den Karlsruher Retweet Bot
##
## crontab -e:
## */5 * * * * /path/to/karlsruher/run-cron.sh >/dev/null 2>&1
##

import os
import sys
import karlsruher


if len(sys.argv) == 2 and sys.argv[1] == "-test":
	import mock
	twitter = mock.twitter()

else:
	import tweepy
	execfile(os.path.dirname(os.path.realpath(__file__)) + '/credentials.py')
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
	twitter = tweepy.API(auth)

runner = karlsruher.Bot(twitter)
runner.readMentions()
