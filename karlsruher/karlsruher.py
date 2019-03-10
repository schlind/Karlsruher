# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher
"""
Karlsruher Twitter Robot
"""

from .common import StopWatch
from .robot import Robot


class Karlsruher(Robot):
    """
    A robot to perform the famous retweet feature.
    """

    # The related tweet_type in the Brain:
    tweet_type = 'mention'

    # Advisors:
    # A list of Twitter users who can switch
    # retweets on/off by tweeted commands.
    advisors = []

    # Language:
    reply_advice_sleep = 'Ok %name%, ich retweete nicht mehr... (Automatische Antwort)'
    reply_advice_wakeup = 'Ok %name%, ich retweete wieder... (Automatische Antwort)'

    def perform(self):
        """
        Read latest mentions and delegate actions.
        """
        self.lock.acquire()
        watch = StopWatch()
        self.logger.info('Fetching advisors and reading mentions...')
        try:
            self.advisors = []
            for advisor in self.twitter.list_members(self.twitter.screen_name, 'advisors'):
                self.advisors.append(str(advisor.id))
            for mention in self.twitter.mentions_timeline():
                self.read_mention(mention)
        finally:
            self.logger.info('Reading mentions done, took %s.', watch.elapsed())
            self.lock.release()

    def read_mention(self, tweet):
        """
        Read a single mention and apply actions, only once.

        The applied action can either be "read_mention",
        "advice_action" or "retweet_action".

        :param tweet: The mention to be read.
        :return: True if the mention was read for the first time
            or False if the mention was already read before.
        """
        tweet_log = '@{}/{}'.format(tweet.user.screen_name, tweet.id)

        if str(tweet.user.screen_name) == str(self.twitter.screen_name):
            self.logger.debug('%s is by me, no action.', tweet_log)
            return False

        if self.brain.has_tweet(self.tweet_type, tweet.id):
            self.logger.info('%s read before, no action.', tweet_log)
            return False

        applied_action = 'read_mention'
        try:
            for apply_action in [self.advice_action, self.retweet_action]:
                if apply_action(tweet):
                    applied_action = apply_action.__name__
                    break
        finally:
            self.brain.add_tweet(self.tweet_type, tweet, applied_action)
            self.logger.info('%s applied %s.', tweet_log, applied_action)

        return True

    def advice_action(self, tweet):
        """
        Take an advice.

        Users in Twitter list "advisors" can advice the
        bot to either go to sleep (no more retweeting)
        or to wake up (retweet again).

        :param tweet: The advice to be read.
        :return: True if an advice was taken, otherwise False
        """
        if str(tweet.user.id) not in self.advisors:
            self.logger.debug('@%s is not an advisor.', tweet.user.screen_name)
            return False

        message = str(tweet.text)
        trigger = '@{}!'.format(self.twitter.screen_name.lower())

        if not message.lower().startswith(trigger):
            self.logger.debug('@%s gave no advice.', tweet.user.screen_name)
            return False

        advice = message[len(trigger):].strip()

        if advice.lower().startswith('geh schlafen!'):
            self.logger.info('Going to sleep for @%s.', tweet.user.screen_name)
            self.brain.set('retweet.disabled', True)
            self.reply(tweet, self.reply_advice_sleep)
            return True

        if advice.lower().startswith('wach auf!'):
            self.logger.info('Waking up for @%s.', tweet.user.screen_name)
            self.brain.set('retweet.disabled', None)
            self.reply(tweet, self.reply_advice_wakeup)
            return True

        return False

    def retweet_action(self, tweet):
        """
        Maybe retweet the given tweet.

        :param tweet: The tweet to maybe retweet
        :return: True if the retweet action applied, otherwise False
        """
        if self.brain.get('retweet.disabled'):
            self.logger.debug('I am sleeping and not retweeting.')
            return False

        if not self.brain.has_follower(tweet.user.id):
            self.logger.debug('@%s not following, no retweet.', tweet.user.screen_name)
            return False

        if str(tweet.user.protected) == 'True':
            self.logger.debug('@%s is protected, no retweet.', tweet.user.screen_name)
            return False

        if str(tweet.in_reply_to_status_id) != 'None':
            self.logger.debug('@%s wrote reply, no retweet.', tweet.user.screen_name)
            return False

        self.logger.debug('@%s retweeting.', tweet.user.screen_name)
        self.retweet(tweet)
        return True
