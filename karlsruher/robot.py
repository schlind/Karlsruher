'''
Twitter Robot
'''

import logging
import os
import sys
import time

from .brain import Brain
from .common import Lock
from .twitter import Twitter, TwitterException
from .__version__ import __version__


class Robot:
    '''Base class for Twitter robots'''

    # Enable writing Twitter API calls:
    act_on_twitter = True

    # Delay between writing Twitter API calls:
    act_delay = 3.275


    def __init__(self, home, brain=None, twitter=None):
        '''
        :param home: The home directory
        :param brain: Optional, a mocked Brain instance for testing
        :param twitter: Optional, a mocked Twitter instance for testing
        '''
        if not os.path.isdir(home):
            raise NotADirectoryError('Specified home "{}" not found.'.format(home))

        self.logger = logging.getLogger(__class__.__name__)
        self.logger.info('Karlsruher Twitter Robot v%s', __version__)

        self.lock = Lock('{}/lock'.format(home))
        self.sleep = Lock('{}/sleeping'.format(home))

        self.twitter = twitter if twitter else Twitter('{}/auth.yaml'.format(home))
        self.logger.info('Hello, my name is @%s.', self.twitter.screen_name)

        self.advisors = []
        for advisor in self.twitter.list_members(self.twitter.screen_name, 'advisors'):
            self.logger.debug('@%s is an advisor.', advisor.screen_name)
            self.advisors.append(str(advisor.id))
        self.logger.info('I am having %s advisors.', len(self.advisors))

        if '-noact' in sys.argv:
            self.act_on_twitter = False

        if not self.is_awake():
            self.logger.info('SLEEPING: I am NOT acting on Twitter!')

        self.brain = brain if brain else Brain('{}/brain'.format(home))
        self.logger.info(self.brain)



    def delay(self):
        '''Provide a second sleep'''
        time.sleep(self.act_delay)

    def housekeeping(self):
        '''Import followers and friends from Twitter into the brain'''
        self.lock.acquire('Housekeeping! This may take a while...')
        try:
            self.logger.info('Fetching followers...')
            self.brain.import_users('follower', self.twitter.follower_ids)
            self.logger.info('Fetching friends...')
            self.brain.import_users('friend', self.twitter.friend_ids)
        finally:
            self.lock.release('Housekeeping done')



    def is_awake(self):
        ''':return: True when awake, otherwise false'''
        return self.act_on_twitter and not self.sleep.is_acquired()

    def wake_up(self, reason='no reason'):
        ''':param reason: The reason to wake up'''
        self.sleep.release('Waking up for {}'.format(reason))

    def go_sleep(self, reason='no reason'):
        ''':param reason: The reason to fall asleep'''
        if not self.sleep.is_acquired():
            self.sleep.acquire('Going to sleep for {}'.format(reason))
        else:
            self.logger.info('Already Sleeping.')



    def is_follower(self, user_id):
        '''
        :param user_id: The user ID to check
        :return: True if the user is a follower, otherwise False
        '''
        return self.brain.find_user('follower', user_id)

    def is_friend(self, user_id):
        '''
        :param user_id: The user ID to check
        :return: True if the user is a friend, otherwise False
        '''
        return self.brain.find_user('friend', user_id)



    def has_tweet(self, tweet_id):
        '''
        :param tweet_id: The tweet ID to check
        :return: True if the tweet exists, otherwise False
        '''
        return self.brain.find_tweet(tweet_id)

    def remember_tweet(self, tweet_id):
        ''':param tweet_id: The tweet ID to remember'''
        self.brain.store_tweet(tweet_id)



    @staticmethod
    def tweet_str(tweet):
        '''
        :param tweet: The tweet to stringify
        :return: The tweet as string "@USERNAME/TWEET_ID"
        '''
        return '@{}/{}'.format(tweet.user.screen_name, tweet.id)



    def get_new_mentions(self):
        ''':return: New mentions without possible advises'''
        mentions = []
        for mention in self.twitter.mentions_timeline():

            if str(mention.user.screen_name) == str(self.twitter.screen_name):
                # Ignore mentions from myself:
                self.logger.debug('%s was by me.', Robot.tweet_str(mention))
                continue

            if self.has_tweet(mention.id):
                # Do not read a mention twice:
                self.logger.debug('%s was read before.', Robot.tweet_str(mention))
                continue

            if self.apply_advise(mention):
                # Remember read advises:
                self.remember_tweet(mention.id)

            else:
                mentions.append(mention)

        return mentions

    # pylint: disable=lost-exception
    def apply_advise(self, mention):
        '''
        :param mention: The mention to expect an advise from
        :return: True if an advise was followed, otherwise False
        '''
        if str(mention.user.id) not in self.advisors:
            self.logger.debug('@%s is not an advisor.', mention.user.screen_name)
            return False

        trigger = '@{}!'.format(self.twitter.screen_name.lower())
        if not mention.text.lower().startswith(trigger):
            self.logger.debug('@%s gave no advise trigger.', mention.user.screen_name)
            return False

        advise = mention.text[len(trigger):].strip()

        if advise.lower().startswith('START'.lower()):
            self.logger.debug('@%s gave advise START.', mention.user.screen_name)
            self.wake_up(mention.user.screen_name)
            self.reply(mention, 'Ok, ich starte... (auto-reply)')
            return True

        if advise.lower().startswith('STOP'.lower()):
            self.logger.debug('@%s gave advise STOP.', mention.user.screen_name)
            self.go_sleep(mention.user.screen_name)
            self.reply(mention, 'Ok, ich stoppe... (auto-reply)')
            return True

        self.logger.debug('@%s gave no advise.', mention.user.screen_name)
        return False



    def tweet(self, text, in_reply_to_status_id=None):
        ''':param text: The text to tweet'''
        if self.act_on_twitter:
            try:
                self.logger.info('Tweet: "%s"', text)
                response = self.twitter.update_status(
                    text=text,
                    in_reply_to_status_id=in_reply_to_status_id
                )
                self.logger.debug('Tweet response: %s', response)
            except TwitterException as twitter_exception:
                self.logger.debug(twitter_exception)
        else:
            self.logger.info('I HAVE NOT tweeted on Twitter!')

    def reply(self, tweet, text):
        '''
        :param tweet: The mention to reply to
        :param text: The text to reply
        '''
        self.tweet(self.build_reply_status(tweet, text), tweet.id)

    def build_reply_status(self, tweet, text):
        '''
        Twitter wants a reply to contain the user.screen_name of the
        origin tweet in the reply status text.

        :param tweet: The tweet to reply to
        :param text: The text to reply
        :return: The text to reply with definitely mention of the origin
        '''
        required_name = '@{}'.format(tweet.user.screen_name)
        if required_name not in text:
            self.logger.debug('Adding %s to text"', required_name)
            text = '{0} {1}'.format(required_name, text)
        return text
