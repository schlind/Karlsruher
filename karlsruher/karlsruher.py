'''
Karlsruher Twitter Robot Personality
'''

from .robot import Robot
from .twitter import TwitterException


class Karlsruher(Robot):
    '''Robot to perform the famous @Karlsruher retweet feature'''

    def feature_retweets(self):
        '''Read new mentions to apply retweets'''
        self.lock.acquire('Reading mentions for retweets...')
        try:
            for mention in self.get_new_mentions():
                try:
                    if self.retweet_applies(mention):
                        self.logger.info('%s retweeted.', Robot.tweet_str(mention))
                    else:
                        self.logger.info('%s ignored.', Robot.tweet_str(mention))
                except TwitterException as twitter_error:
                    self.logger.debug(twitter_error)
                finally:
                    # All mentions handled by this feature are remembered:
                    self.remember_tweet(mention.id)
        finally:
            self.lock.release('Reading mentions done')

    def retweet_applies(self, mention):
        '''
        :param mention: The mention to retweet
        :return: True when a retweet was applied, otherwise False
        '''

        # Ignore mentions from myself:
        if str(mention.user.screen_name) == str(self.twitter.screen_name):
            self.logger.debug('@%s is me.', mention.user.screen_name)
            return False

        # Can't retweet protected users:
        if str(mention.user.protected) == 'True':
            self.logger.debug('@%s is protected.', mention.user.screen_name)
            return False

        # Never retweet replies:
        if str(mention.in_reply_to_status_id) != 'None':
            self.logger.debug('@%s wrote reply.', mention.user.screen_name)
            return False

        # Only followers get retweeted:
        if not self.is_follower(mention.user.id):
            self.logger.debug('@%s not following.', mention.user.screen_name)
            return False

        # Would retweet but do not so while sleeping:
        if not self.is_awake():
            self.logger.debug('@%s read during sleep.', mention.user.screen_name)
            return True

        try:
            # Retweeting on Twitter:
            self.logger.debug('Retweeting: %s', Robot.tweet_str(mention))
            response = self.twitter.retweet(mention.id)
            self.logger.debug('Retweet response: %s', response)
        except TwitterException as twitter_error:
            self.logger.debug(twitter_error)
        finally:
            # Do not flood Twitter with retweets:
            self.delay()

        return True
