'''
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher

Manually authorize (Website + PIN) a new Access-Token
for a given Consumer-Token via Twitter API

'''

import tweepy

CONSUMER_KEY = input('Your Twitter API Consumer Key: ').strip()
CONSUMER_SECRET = input('Your Twitter API Consumer Secret: ').strip()

OAUTHHANDLER = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
AUTHORIZATION_URL = OAUTHHANDLER.get_authorization_url()

print('Please authorize: ', AUTHORIZATION_URL)
VERIFIER = input('Enter PIN: ').strip()

OAUTHHANDLER.get_access_token(VERIFIER)
print("TWITTER_ACCESS_KEY = '%s'" % OAUTHHANDLER.access_token.key)
print("TWITTER_ACCESS_SECRET = '%s'" % OAUTHHANDLER.access_token.secret)
