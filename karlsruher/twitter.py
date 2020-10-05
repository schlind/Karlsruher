'''
Twitter API Client
'''

import logging
import tweepy

from .tweepyx import tweepyx


class Twitter: # pragma: no cover
    '''Proxy for tweepy'''

    def __init__(self, auth_yaml_file_path):
        ''':param auth_yaml_file_path: The credentials file'''
        self.logger = logging.getLogger(__class__.__name__)
        self.api = tweepyx.API(auth_yaml_file_path, create_file_on_demand=False)
        self.screen_name = self.me().screen_name

    # pylint: disable=invalid-name
    # because Twitter named it that way
    def me(self):
        ''':return: The "me" object from Twitter'''
        try:
            return self.api.me()
        except tweepy.error.TweepError as tweep_error:
            self.logger.error(tweep_error)
            raise TwitterException from tweep_error

    def mentions_timeline(self): # pragma: no cover
        ''':return: The mentions timeline'''
        try:
            return self.api.mentions_timeline(count=200)
        except tweepy.error.TweepError as tweep_error:
            self.logger.error(tweep_error)
            raise TwitterException from tweep_error

    def list_members(self, screen_name, list_slug): # pragma: no cover
        ''':return: List of members of the specified list'''
        try:
            self.api.list_members.pagination_mode = 'cursor'
            for member in tweepy.Cursor(
                    self.api.list_members, screen_name, list_slug
            ).items():
                yield member
        except tweepy.error.TweepError as tweep_error:
            self.logger.error(tweep_error)
            raise TwitterException from tweep_error

    def follower_ids(self): # pragma: no cover
        ''':return: List of twitter user_ids who follow the robot'''
        try:
            self.api.followers_ids.pagination_mode = 'cursor'
            for follower_id in tweepy.Cursor(self.api.followers_ids).items():
                yield follower_id
        except tweepy.error.TweepError as tweep_error:
            self.logger.error(tweep_error)
            raise TwitterException from tweep_error

    def friend_ids(self): # pragma: no cover
        ''':return: List of twitter user_ids who the robot follows'''
        try:
            self.api.friends_ids.pagination_mode = 'cursor'
            for friend_id in tweepy.Cursor(self.api.friends_ids).items():
                yield friend_id
        except tweepy.error.TweepError as tweep_error:
            self.logger.error(tweep_error)
            raise TwitterException from tweep_error

    def retweet(self, tweet_id): # pragma: no cover
        '''
        :param tweet_id: The tweet ID to retweet
        :return: The API response
        '''
        try:
            return self.api.retweet(tweet_id)
        except tweepy.error.TweepError as tweep_error:
            self.logger.error(tweep_error)
            raise TwitterException from tweep_error

    def update_status(self, text, in_reply_to_status_id=None): # pragma: no cover
        '''
        :param text: The text to tweet
        :param in_reply_to_status_id: Optional, if tweeting a reply
        :return: The API response
        '''
        try:
            if in_reply_to_status_id:
                return self.api.update_status(
                    in_reply_to_status_id=in_reply_to_status_id,
                    auto_populate_reply_metadata=True,
                    status=text
                )
            return self.api.update_status(status=text)
        except tweepy.error.TweepError as tweep_error:
            self.logger.error(tweep_error)
            raise TwitterException from tweep_error

class TwitterException(Exception):
    '''Mask tweepy.error.TweepError'''
