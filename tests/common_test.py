'''
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher
'''

from unittest import mock, TestCase
import tempfile

import karlsruher


class LockTest(TestCase):

    def setUp(self):
        self.lock = karlsruher.Lock(tempfile.gettempdir() + '/LockTest.tmp')

    def tearDown(self):
        self.lock.release()

    def test_can_indicate_lock(self):
        self.assertFalse(self.lock.is_present())

    def test_can_acquire_and_indicate_lock(self):
        self.assertTrue(self.lock.acquire())
        self.assertTrue(self.lock.is_present())

    def test_can_acquire_lock_only_once(self):
        self.assertTrue(self.lock.acquire())
        self.assertFalse(self.lock.acquire())

    def test_can_release_lock(self):
        self.lock.release()
        self.assertFalse(self.lock.is_present())


class StopWatchTest(TestCase):

    def test_can_read_elapsed_time(self):
        self.assertEqual('0:00:00.00', str(karlsruher.StopWatch().elapsed())[:10])