'''
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher
'''

import os
import tweepy

##
##
class Twitter:

    """Proxy required API calls."""

    def __init__(self, credentials = None):
        self.api = None

    #def connect(self, credentials):

        if not os.path.isfile(credentials):
            raise Exception('''Missing credentials file!

Please create file "{}" with contents:

TWITTER_CONSUMER_KEY = 'Your Consumer Key'
TWITTER_CONSUMER_SECRET = 'Your Consumer Secret'
TWITTER_ACCESS_KEY = 'Your Access Key'
TWITTER_ACCESS_SECRET = 'Your Access Secret'

'''.format(credentials))

        from credentials import \
            TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, \
            TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET

        oauth = tweepy.OAuthHandler(
            TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET
        )
        oauth.set_access_token(TWITTER_ACCESS_KEY, TWITTER_ACCESS_SECRET)

        self.api = tweepy.API(
            oauth, compression=True,
            wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True
        )


    def me(self):
        return self.api.me()

    def mentions_timeline(self):
        return self.api.mentions_timeline()

    def list_advisors(self):
        self.api.list_members.pagination_mode = 'cursor'
        for advisor in tweepy.Cursor(
                self.api.list_members, self.me().screen_name, 'advisors'
        ).items():
            yield advisor

    def followers(self):
        self.api.followers.pagination_mode = 'cursor'
        for follower in tweepy.Cursor(self.api.followers).items():
            yield follower

    def friends(self):
        self.api.friends.pagination_mode = 'cursor'
        for friend in tweepy.Cursor(self.api.friends).items():
            yield friend

    def retweet(self, tweet):
        return self.api.retweet(tweet.id)

    def update_status(self, status, in_reply_to_status_id=None):
        if in_reply_to_status_id:
            return self.api.update_status(
                in_reply_to_status_id=in_reply_to_status_id,
                status=status
            )
        return self.api.update_status(status=status)
