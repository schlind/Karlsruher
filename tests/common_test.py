'''
LockTest StopWatchTest
'''

import tempfile
from unittest import TestCase

from karlsruher.common import Lock, LockException
from karlsruher.common import StopWatch

class LockTest(TestCase):
    '''Test the Lock'''

    def setUp(self):
        self.lock = Lock(tempfile.gettempdir() + '/LockTest.tmp')

    def tearDown(self):
        self.lock.release()

    def test_is_initially_unlocked(self):
        '''Lock must not be present'''
        self.assertFalse(self.lock.is_acquired())
        self.assertEqual('Lock is free.',str(self.lock))

    def test_can_acquire_and_release(self):
        '''Lock must be acquired and released'''
        self.lock.acquire()
        self.assertEqual('Lock is acquired.',str(self.lock))
        self.assertTrue(self.lock.is_acquired())
        self.lock.release()
        self.assertFalse(self.lock.is_acquired())

    def test_can_acquire_once_only(self):
        '''Lock must raise LockException'''
        self.lock.acquire()
        self.assertRaises(LockException, self.lock.acquire)

class StopWatchTest(TestCase):
    '''Test the StopWatch'''

    def test_can_read_elapsed_time(self):
        '''StopWatch must produce human readable output'''
        self.assertEqual('0:00:00.00', StopWatch().elapsed()[:10])
