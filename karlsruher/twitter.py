'''
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher

Twitter client

'''

import os
import tweepy

##
##
class Twitter:

    """Proxy required API calls."""

    def __init__(self, credentials=None):

        if not os.path.isfile(credentials):
            raise Exception('''Please create file "{}" with contents:

TWITTER_CONSUMER_KEY = 'Your Consumer Key'
TWITTER_CONSUMER_SECRET = 'Your Consumer Secret'
TWITTER_ACCESS_KEY = 'Your Access Key'
TWITTER_ACCESS_SECRET = 'Your Access Secret'

'''.format(credentials))

        # pylint: disable=import-error
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
        '''Provide "me" user object from Twitter.'''
        return self.api.me()

    def mentions_timeline(self):
        '''Provide "mentions_timeline" from Twitter.'''
        return self.api.mentions_timeline()

    def list_advisors(self):
        '''Provide "list_members" of list "advisors" from Twitter.'''
        self.api.list_members.pagination_mode = 'cursor'
        for advisor in tweepy.Cursor(
                self.api.list_members, self.me().screen_name, 'advisors'
        ).items():
            yield advisor

    def followers(self):
        '''Provide "followers" from Twitter.'''
        self.api.followers.pagination_mode = 'cursor'
        for follower in tweepy.Cursor(self.api.followers).items():
            yield follower

    def friends(self):
        '''Provide "friends" from Twitter.'''
        self.api.friends.pagination_mode = 'cursor'
        for friend in tweepy.Cursor(self.api.friends).items():
            yield friend

    def retweet(self, tweet):
        '''Send "retweet" to Twitter.'''
        return self.api.retweet(tweet.id)

    def update_status(self, status, in_reply_to_status_id=None):
        '''Send "update_status" to Twitter.'''
        if in_reply_to_status_id:
            return self.api.update_status(
                in_reply_to_status_id=in_reply_to_status_id,
                status=status
            )
        return self.api.update_status(status=status)
