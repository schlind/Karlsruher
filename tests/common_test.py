'''
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher
'''

import tempfile
from unittest import TestCase

import karlsruher


class LockTest(TestCase):

    def setUp(self):
        self.lock = karlsruher.common.Lock(tempfile.gettempdir() + '/LockTest.tmp')

    def tearDown(self):
        self.lock.release()

    def test_can_indicate_lock(self):
        self.assertFalse(self.lock.is_present())

    def test_can_acquire_and_indicate_lock(self):
        self.assertTrue(self.lock.acquire())
        self.assertTrue(self.lock.is_present())

    def test_can_acquire_lock_only_once(self):
        self.assertTrue(self.lock.acquire())
        self.assertRaises(karlsruher.common.LockException, self.lock.acquire)

    def test_can_release_lock(self):
        self.assertTrue(self.lock.acquire())
        self.lock.release()
        self.assertFalse(self.lock.is_present())


class StopWatchTest(TestCase):

    def test_can_read_elapsed_time(self):
        self.assertEqual(
            '0:00:00.00', karlsruher.common.StopWatch().elapsed()[:10]
        )
