# Karlsruher Retweet Robot
# https://github.com/schlind/Karlsruher
"""
*knockknock* Housekeeping!
"""

from .common import StopWatch
from .robot import Robot


class HouseKeeper(Robot):
    """
    A robot to perform internal housekeeping tasks.
    """

    def perform(self):
        """
        A housekeeping session imports followers and friends
        from Twitter.

        Due to API rate limits this may take up to 1 hour per
        1000 followers/friends.
        """
        self.lock.acquire()
        watch = StopWatch()
        self.logger.info('Housekeeping! This may take a while...')
        try:
            self.brain.import_followers(self.twitter.followers)
            self.brain.import_friends(self.twitter.friends)
        finally:
            self.logger.info('Housekeeping done, took %s.', watch.elapsed())
            self.lock.release()
