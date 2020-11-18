'''
Karlsruher Twitter Robot
'''

import logging
import os
import sys
import time

import tweepy
from tweepy.error import TweepError

from .tweepyx import tweepyx
from .brain import Brain
from .__version__ import __version__



CONSOLE_HELP_TEXT = '''

Karlsruher Twitter Robot v{}

Required argument:

    --home=PATH     specify a home directory for 
                    auth.yaml, brain and log files

Usage Examples:
    Do housekeeping (fetch followers) with:
        $ karlsruher --home=PATH -housekeeping

    Retweet follower's mentions with:
        $ karlsruher --home=PATH -retweet

Optional, just append:
    -debug          sets console logging to DEBUG
    -version        print version information and exit
    -help           you are reading this right now


Cheers!
'''.strip().format(__version__)



class Karlsruher:
    '''
    Karlsruher Twitter Robot.
    '''

    # Delay between retweets in seconds:
    delay = 3.275


    def __init__(self, home=None, brain=None, api=None):
        '''
        Bootstrap instance and connect to Twitter.

        :param home: Optional, the home directory, taken from commandline.
        :param brain: For testing, a mocked Brain instance.
        :param api: For testing, a mocked Tweepy API instance.
        '''

        # Check for a home directory:
        if not home:
            for arg in sys.argv:
                if not home and arg.startswith('--home='):
                    home = arg[len('--home='):]
        if not home:
            raise NotADirectoryError('Please specify a home directory with "--home=/PATH".')
        if not os.path.isdir(home):
            raise NotADirectoryError('Specified home "{}" not found.'.format(home))

        # Start logging:
        self.logger = logging.getLogger(__class__.__name__)
        self.logger.info('Karlsruher Twitter Robot v%s', __version__)

        # Check and create lock file:
        self.lockfile = '{}/lock'.format(home)
        if os.path.isfile(self.lockfile):
            raise RuntimeError('Locked by "{}".'.format(self.lockfile))
        open(self.lockfile, 'w').close()

        # Connect to brain:
        self.brain = brain if brain else Brain('{}/brain'.format(home))

        # Connect to Twitter and determine own screen_name:
        self.api = api if api else tweepyx.API('{}/auth.yaml'.format(home))
        self.screen_name = self.api.me().screen_name

        # Fetch advisors from list to brain:
        self.brain.forget('advisor')
        try:
            for member in self.api.list_members(self.screen_name, 'advisors'):
                self.brain.store('advisor', member.id)
        except TweepError: # pragma: no cover
            self.logger.error('Could not fetch advisors from list.')

        # Log status:
        self.logger.info(self)



    def __repr__(self):
        '''
        :return: String representation.
        '''
        return 'Hello, my name is @{0}! {1}'.format(self.screen_name, self.brain)



    def __del__(self):
        '''
        Remove lockfile on destruction.
        '''
        if hasattr(self, 'lockfile') and os.path.isfile(self.lockfile):
            os.remove(self.lockfile)



    def housekeeping(self):
        '''
        Import followers and friends from Twitter into the brain.
        '''
        self.logger.info('Housekeeping...')
        try:

            self.brain.forget('follower')
            self.api.followers_ids.pagination_mode = 'cursor'
            for follower_id in tweepy.Cursor(self.api.followers_ids).items():
                self.brain.store('follower', follower_id)

            self.brain.forget('friend')
            self.api.friends_ids.pagination_mode = 'cursor'
            for friend_id in tweepy.Cursor(self.api.friends_ids).items():
                self.brain.store('friend', friend_id)

        except TweepError: # pragma: no cover
            self.logger.error('Could not fetch followers and/or friends.')
        finally:
            self.logger.info(self.brain)
            self.logger.info('Housekeeping done.')



    def is_sleeping(self):
        ''':return: True when sleeping, otherwise False.'''
        return self.brain.has('sleep','sleep')



    def go_sleep(self, reason='no reason'):
        ''':param reason: The reason to fall asleep.'''
        if not self.brain.has('sleep','sleep'):
            self.logger.info('Going to sleep for %s', reason)
            self.brain.store('sleep', 'sleep', reason)
        else:
            self.logger.info('Already Sleeping.')



    def wake_up(self, reason='no reason'):
        ''':param reason: The reason to wake up.'''
        self.logger.info('Waking up for %s', reason)
        self.brain.forget('sleep', 'sleep')



    def apply_advise(self, mention):
        '''
        :param mention: The mention to expect an advise from.
        :return: True if an advise was followed, otherwise False.
        '''
        if not self.brain.has('advisor', mention.user.id):
            return False

        trigger = '@{}!'.format(self.screen_name.lower())
        if mention.text.lower().startswith(trigger):

            advise = mention.text[len(trigger):].strip()

            if advise.lower().startswith('START'.lower()):
                self.brain.store('tweet', mention.id)
                self.wake_up(mention.user.screen_name)
                self.reply(mention, 'Ok, starting... (auto-reply)')
                return True

            if advise.lower().startswith('STOP'.lower()):
                self.brain.store('tweet', mention.id)
                self.go_sleep(mention.user.screen_name)
                self.reply(mention, 'Ok, stopping... (auto-reply)')
                return True

        return False



    def latest_mentions(self, count=200):
        '''
        :param count: Optional number of mentions to fetch.
        :return: Latest mentions *without* mentions by myself, mentions that
                    contain advises and mentions that were read before.
        '''
        mentions = []
        for mention in self.api.mentions_timeline(count=count):
            if str(mention.user.screen_name) == str(self.screen_name):
                continue
            if self.brain.has('tweet', mention.id):
                continue
            if self.apply_advise(mention):
                continue
            mentions.append(mention)
        return mentions



    def retweet(self, tweet):
        '''
        :param tweet: The tweet to retweet.
        '''
        self.logger.info('Retweeting: %s ...', tweet.user.screen_name)
        try:
            return self.api.retweet(tweet.id)
        except TweepError as tweep_error: # pragma: no cover
            self.logger.error(tweep_error)
        finally:
            time.sleep(self.delay)



    def tweet(self, text, in_reply_to_status_id=None):
        '''
        :param text: The text to tweet.
        :param in_reply_to_status_id:
        :return:
        '''
        self.logger.info('Tweeting: "%s"', text)
        try:
            return self.api.update_status(
                in_reply_to_status_id=in_reply_to_status_id,
                text=text
            )
        except TweepError as tweep_error: # pragma: no cover
            self.logger.error(tweep_error)
        finally:
            time.sleep(self.delay)



    def reply(self, tweet, text):
        '''
        :param tweet: The tweet to reply to.
        :param text: The text to reply.
        '''
        # Twitter wants a reply to contain the user.screen_name of the
        # origin tweet in the reply status text:
        required_name = '@{}'.format(tweet.user.screen_name)
        if required_name not in text:
            text = '{0} {1}'.format(required_name, text)
        self.tweet(in_reply_to_status_id=tweet.id, text=text)


## Behavior:

def read_mentions(karlsruher):
    '''
    Read mentions to console log.
    :param karlsruher: A Karlsruher instance.
    '''
    karlsruher.logger.info('Reading mentions...')

    for mention in karlsruher.latest_mentions():

        karlsruher.brain.store('tweet', mention.id)

        karlsruher.logger.info(
            'Reading mention @%s %s:\n%s\n',
            mention.user.screen_name,
            mention.id,
            mention.text
        )

    karlsruher.logger.info('Reading mentions done.')



def retweet_mentions(karlsruher):
    '''
    Retweet mentions but not replies, by non-protected followers.
    :param karlsruher: A Karlsruher instance.
    '''
    karlsruher.logger.info('Reading mentions for retweets...')

    for mention in karlsruher.latest_mentions():

        karlsruher.brain.store('tweet', mention.id)

        if str(mention.in_reply_to_status_id) != 'None':
            continue

        if str(mention.user.protected) == 'True':
            continue

        if karlsruher.is_sleeping():
            continue

        if karlsruher.brain.has('follower', mention.user.id):
            karlsruher.retweet(mention)

    karlsruher.logger.info('Reading mentions for retweets done.')
