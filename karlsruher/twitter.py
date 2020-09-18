# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher
"""
Module providing Twitter client
"""

import tweepy

from .common import KarlsruhError
from .tweepyx import tweepyx


class Twitter:
    """
    Proxy Twitter API calls.
    """

    def __init__(self, auth_yaml_file_path):
        """
        :param auth_yaml_file_path:
        """
        self.api = tweepyx.API(auth_yaml_file_path, create_file=False)
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
            raise KarlsruhError('API call "me":', tweep_error)

    def mentions_timeline(self): # pragma: no cover
        """
        Provide "mentions_timeline" from Twitter.

        :return: List of the latest tweets from the mentions timeline
        """
        try:
            return self.api.mentions_timeline()
        except tweepy.error.TweepError as tweep_error:
            raise KarlsruhError('API call "mentions_timeline":', tweep_error)

    def list_members(self, screen_name, list_slug): # pragma: no cover
        """
        Provide "list_members" from Twitter.

        :return: List of twitter users who are a member of the specified list
        """
        try:
            self.api.list_members.pagination_mode = 'cursor'
            for member in tweepy.Cursor(
                    self.api.list_members, screen_name, list_slug
            ).items():
                yield member
        except tweepy.error.TweepError as tweep_error:
            raise KarlsruhError('API call "list_members":', tweep_error)

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
            raise KarlsruhError('API call "followers":', tweep_error)

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
            raise KarlsruhError('API call "friends":', tweep_error)

    def retweet(self, tweet_id): # pragma: no cover
        """
        Retweet the given tweet.

        :param tweet_id: The tweet_id to retweet
        :return: The API response
        """
        try:
            return self.api.retweet(tweet_id)
        except tweepy.error.TweepError as tweep_error:
            raise KarlsruhError('API call "retweet":', tweep_error)

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
            raise KarlsruhError('API call "update_status":', tweep_error)
