# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher
"""
Module providing Config and Robot
"""

import logging
import os

from .brain import Brain
from .common import Lock
from .twitter import Twitter
from .version import __version__


class Config:
    """
    Provide runtime configuration values.
    """
    def __init__(self, home, do_reply=False, do_retweet=False):
        """
        Create instance with the given home directory.

        :param home: The home directory.
        :param do_reply: Give True to send replies
        :param do_retweet: Give True to perform retweets
        :raises NotADirectoryError: if the home directory is not present
        """
        if not os.path.isdir(home):
            raise NotADirectoryError('Specified home "{}" not found.'.format(home))

        self.home = home
        self.do_reply = do_reply
        self.do_retweet = do_retweet


class Robot:
    """
    Base class for Twitter robots.
    """
    def __init__(self, config, brain=None, twitter=None):
        """
        Create instance with the specified config.

        Give optional brain and twitter mock objects for testing purposes.

        :type config: Config
        :param config: The home directory and other settings

        :type brain: Brain
        :param brain: Optional, a mocked Brain instance for testing

        :type twitter: Twitter
        :param twitter: Optional, a mocked Twitter instance for testing
        """
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.info('Karlsruher Twitter Robot v%s', __version__)

        self.config = config
        self.lock = Lock('{}/lock'.format(self.config.home))

        self.twitter = twitter if twitter else Twitter('{}/auth.yaml'.format(self.config.home))
        self.logger.info('Hello, my name is @%s.', self.twitter.screen_name)

        self.brain = brain if brain else Brain('{}/brain'.format(self.config.home))
        self.logger.info('Brain metrics: %s', self.brain.metrics())

    # Abstract:

    def perform(self):
        """
        Whatever task a robot performs, it's meant to start
        here and should be implemented in subclasses.
        """
        self.logger.debug('Nothing implemented here.')

    # Convenience methods:

    def is_follower(self, user_id):
        """
        Indicate whether the user with the given user_id follows.

        :param user_id: The user_id to check
        :return: True when the given user_id is a follower
        """
        return self.brain.has_user('follower', user_id)


    def reply(self, tweet, status):
        """
        Send a reply to the given tweet.

        Twitter want's the origin screen_name to be mentioned in
        the status text when replying, otherwise it raises an error.

        The placeholder "%name%" in a status text will be replaced
        with the required screen_name.

        :param tweet: The tweet to reply to
        :param status: The status (text) to reply
        """
        # Prepare the required name to reply to:
        required_name = '@{}'.format(tweet.user.screen_name)
        # Replace placeholder, if any:
        if '%name%' in status:
            status = status.replace('%name%', required_name)
        # If still not present, prepend the required name:
        if required_name not in status:
            status = '{}: {}'.format(required_name, status)

        if self.config.do_reply:
            self.logger.debug('Reply: "%s"', status)
            response = self.twitter.update_status(in_reply_to_status_id=tweet.id, status=status)
            self.logger.debug('Reply response: %s', response)
        else:
            self.logger.debug('Would reply: "%s"', status)

    def retweet(self, tweet):
        """
        Retweet the given tweet.

        :param tweet: The tweet to be retweeted
        """
        if self.config.do_retweet:
            self.logger.debug('Retweet: @%s/%s.', tweet.user.screen_name, tweet.id)
            response = self.twitter.retweet(tweet.id)
            self.logger.debug('Retweet response: %s', response)
        else:
            self.logger.debug('Would retweet: @%s/%s.', tweet.user.screen_name, tweet.id)
