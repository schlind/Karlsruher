# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher

"""
"""

from karlsruher.common import LockException
from karlsruher.housekeeping import HouseKeeper

from .robot_test import RobotTestCase

class HouseKeeperTest(RobotTestCase):
    """
    Test housekeeping.
    """

    def setUp(self):
        super().setUp()
        self.bot = HouseKeeper(
            config=self.test_config,
            brain=self.test_brain,
            twitter=self.mock_twitter
        )

    def test_housekeeping_imports_followers(self):
        """HouseKeeper must import followers."""
        self.bot.perform()
        self.assertEqual(3, len(self.bot.brain.users('follower')))

    def test_housekeeping_imports_friends(self):
        """HouseKeeper must import friends."""
        self.bot.perform()
        self.assertEqual(2, len(self.bot.brain.users('friend')))

    def test_housekeeping_handles_lock(self):
        """HouseKeeper must not ignore a lock."""
        self.bot.lock.acquire()
        self.assertRaises(LockException, self.bot.perform)
        self.assertTrue(self.bot.lock.is_acquired())
