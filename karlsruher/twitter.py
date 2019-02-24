'''
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher

Twitter client

'''

import os
import tweepy
import yaml


class CredentialsException(Exception):

    '''Indicate a problem with credentials file.'''


class Credentials:

    """
twitter:
  consumer:
    key: 'YOUR-CONSUMER-KEY'
    secret: 'YOUR-CONSUMER-SECRET'
  access:
    key: 'YOUR-ACCESS-KEY'
    secret: 'YOUR-ACCESS-SECRET'
    """

    def __init__(self, yaml_file):

        if yaml_file is None or yaml_file.strip() == '':
            raise CredentialsException('Please specify yaml_file.')

        if not os.path.isfile(yaml_file):
            hint = 'Please create file "{}" with contents:{}'
            raise CredentialsException(hint.format(yaml_file, Credentials.__doc__))

        with open(yaml_file, 'r') as stream:
            try:
                read = yaml.load(stream)
                self.consumer_key = read['twitter']['consumer']['key']
                self.consumer_secret = read['twitter']['consumer']['secret']
                self.access_key = read['twitter']['access']['key']
                self.access_secret = read['twitter']['access']['secret']
            except:
                hint = 'Please check file "{}" for contents:{}'
                raise CredentialsException(hint.format(yaml_file, Credentials.__doc__))


class Twitter:

    '''Proxy Twitter API calls.'''


    def __init__(self, credentials_yaml_file):
        '''Use credentials from YAML file to connect to Twitter.'''

        credentials = Credentials(credentials_yaml_file)

        oauth = tweepy.OAuthHandler(
            credentials.consumer_key, credentials.consumer_secret
        )
        oauth.set_access_token(
            credentials.access_key, credentials.access_secret
        )
        self.api = tweepy.API(
            oauth, compression=True,
            wait_on_rate_limit=True, wait_on_rate_limit_notify=True
        )


    # pylint: disable=invalid-name
    ## because Twitter named it.
    def me(self): # pragma: no cover
        '''Provide "me" user object from Twitter.'''
        return self.api.me()

    def mentions_timeline(self): # pragma: no cover
        '''Provide "mentions_timeline" from Twitter.'''
        return self.api.mentions_timeline()

    def list_advisors(self): # pragma: no cover
        '''Provide "list_members" of list "advisors" from Twitter.'''
        self.api.list_members.pagination_mode = 'cursor'
        for advisor in tweepy.Cursor(
                self.api.list_members, self.me().screen_name, 'advisors'
        ).items():
            yield advisor

    def followers(self): # pragma: no cover
        '''Provide "followers" from Twitter.'''
        self.api.followers.pagination_mode = 'cursor'
        for follower in tweepy.Cursor(self.api.followers).items():
            yield follower

    def friends(self): # pragma: no cover
        '''Provide "friends" from Twitter.'''
        self.api.friends.pagination_mode = 'cursor'
        for friend in tweepy.Cursor(self.api.friends).items():
            yield friend

    def retweet(self, tweet): # pragma: no cover
        '''Send "retweet" to Twitter.'''
        return self.api.retweet(tweet.id)

    def update_status(self, status, in_reply_to_status_id=None): # pragma: no cover
        '''Send "update_status" to Twitter.'''
        if in_reply_to_status_id:
            return self.api.update_status(
                in_reply_to_status_id=in_reply_to_status_id,
                status=status
            )
        return self.api.update_status(status=status)
