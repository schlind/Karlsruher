# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher
"""
Module providing a Twitter client
"""

import os
import tweepy
import yaml

from .common import KarlsruhError


class ApiProvider:
    """
    Provide Tweepy API.
    """

    # Example content for HOME/auth.yaml file:
    yaml_content = '''
twitter:
  consumer:
    key: 'YOUR-CONSUMER-KEY'
    secret: 'YOUR-CONSUMER-SECRET'
  access:
    key: 'YOUR-ACCESS-KEY'
    secret: 'YOUR-ACCESS-SECRET'
    '''.strip()

    def __init__(self, auth_yaml_file_path):
        """
        Create instance with given auth.yaml file path.

        :param auth_yaml_file_path: The path to the auth.yaml file
        """
        self.auth_yaml_file_path = auth_yaml_file_path

    def read_credentials(self):
        """
        Read the yaml.

        :return: consumer_key, consumer_secret, access_key, access_secret
        """
        if self.auth_yaml_file_path is None or self.auth_yaml_file_path.strip() == '':
            raise TwittError('Please specify yaml_file.')
        if not os.path.isfile(self.auth_yaml_file_path):
            raise FileNotFoundError(
                'Please create file "{}" with contents:\n{}'.format(
                    self.auth_yaml_file_path, ApiProvider.yaml_content
                )
            )
        with open(self.auth_yaml_file_path, 'r') as file:
            try:
                read = yaml.load(file)
                return (
                    read['twitter']['consumer']['key'],
                    read['twitter']['consumer']['secret'],
                    read['twitter']['access']['key'],
                    read['twitter']['access']['secret']
                )
            except:
                raise TwittError(
                    'Please check file "{}" for proper contents:\n{}'.format(
                        self.auth_yaml_file_path, ApiProvider.yaml_content
                    )
                )

    def oauth_handler(self):
        """
        Provide a tweepy.OAuthHandler.

        :return: The tweepy.OAuthHandler
        """
        consumer_key, consumer_secret, access_key, access_secret = self.read_credentials()
        oauth_handler = tweepy.OAuthHandler(consumer_key, consumer_secret)
        oauth_handler.set_access_token(access_key, access_secret)
        return oauth_handler

    def api(self):
        """
        Provide a tweepy.API.

        :return: The tweepy.API
        """
        return tweepy.API(
            auth_handler=self.oauth_handler(),
            compression=True,
            wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True
        )


class Twitter:
    """
    Proxy Twitter API calls.
    """

    def __init__(self, auth_yaml_file_path):
        """
        :param auth_yaml_file_path:
        """
        self.api = ApiProvider(auth_yaml_file_path).api()
        self.screen_name = self.me().screen_name

    # pylint: disable=invalid-name
    # because Twitter named it that way.
    def me(self): # pragma: no cover
        """
        Provide "me" object from Twitter.

        :return: The "me" object
        """
        try:
            return self.api.me()
        except tweepy.error.TweepError as tweep_error:
            raise TwittError('API call "me":', tweep_error)

    def mentions_timeline(self): # pragma: no cover
        """
        Provide "mentions_timeline" from Twitter.

        :return: List of the latest tweets from the mentions timeline
        """
        try:
            return self.api.mentions_timeline()
        except tweepy.error.TweepError as tweep_error:
            raise TwittError('API call "mentions_timeline":', tweep_error)

    def list_members(self, screen_name, list_slug): # pragma: no cover
        """
        Provide "list_members" from Twitter.

        :return: List of twitter users who are a member of the specified list
        """
        try:
            self.api.list_members.pagination_mode = 'cursor'
            for advisor in tweepy.Cursor(
                    self.api.list_members, screen_name, list_slug
            ).items():
                yield advisor
        except tweepy.error.TweepError as tweep_error:
            raise TwittError('API call "list_members":', tweep_error)

    def followers(self): # pragma: no cover
        """
        Provide "followers" from Twitter.

        :return: List of twitter users who follow the robot
        """
        try:
            self.api.followers.pagination_mode = 'cursor'
            for follower in tweepy.Cursor(self.api.followers).items():
                yield follower
        except tweepy.error.TweepError as tweep_error:
            raise TwittError('API call "followers":', tweep_error)

    def friends(self): # pragma: no cover
        """
        Provide "friends" from Twitter.

        :return: List of twitter users who the robot follows
        """
        try:
            self.api.friends.pagination_mode = 'cursor'
            for friend in tweepy.Cursor(self.api.friends).items():
                yield friend
        except tweepy.error.TweepError as tweep_error:
            raise TwittError('API call "friends":', tweep_error)

    def retweet(self, tweet_id): # pragma: no cover
        """
        Retweet the given tweet.

        :param tweet_id: The tweet_id to retweet
        :return: The API response
        """
        try:
            return self.api.retweet(tweet_id)
        except tweepy.error.TweepError as tweep_error:
            raise TwittError('API call "retweet":', tweep_error)

    def update_status(self, status, in_reply_to_status_id=None): # pragma: no cover
        """
        Update status, send a tweet or reply.

        :param status: The status to tweet
        :param in_reply_to_status_id: Optional, if tweeting a reply
        :return: The API response
        """
        try:
            if in_reply_to_status_id:
                return self.api.update_status(
                    in_reply_to_status_id=in_reply_to_status_id,
                    auto_populate_reply_metadata=True,
                    status=status
                )
            return self.api.update_status(status=status)
        except tweepy.error.TweepError as tweep_error:
            raise TwittError('API call "update_status":', tweep_error)


class TwittError(KarlsruhError):
    """
    Indicate a problem with Twitter.
    """
