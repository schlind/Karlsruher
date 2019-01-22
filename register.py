#!/usr/bin/env python3
##
##
import tweepy
consumer_key = input('Your Twitter API Consumer Key: ').strip()
consumer_secret = input('Your Twitter API Consumer Secret: ').strip()
oauthHandler = tweepy.OAuthHandler(consumer_key, consumer_secret)
authorization_url = oauthHandler.get_authorization_url()
print('Please authorize: ', authorization_url)
verifier = input('Enter PIN: ').strip()
oauthHandler.get_access_token(verifier)
print("TWITTER_ACCESS_KEY = '%s'" % oauthHandler.access_token.key)
print("TWITTER_ACCESS_SECRET = '%s'" % oauthHandler.access_token.secret)
