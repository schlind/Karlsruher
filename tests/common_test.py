'''
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher
'''

from unittest import mock, TestCase
import tempfile

from karlsruher import Lock
from karlsruher import StopWatch


##
##
class LockTest(TestCase):

	def setUp(self):
		self.lock = Lock(tempfile.gettempdir() + '/LockTest.tmp')

	def tearDown(self):
		self.lock.release()

	def test_lock_001_can_indicate(self):
		self.assertFalse(self.lock.is_present())

	def test_lock_002_can_acquire_and_indicate(self):
		self.assertTrue(self.lock.acquire())
		self.assertTrue(self.lock.is_present())

	def test_lock_003_can_acquire_only_once(self):
		self.assertTrue(self.lock.acquire())
		self.assertFalse(self.lock.acquire())

	def test_lock_004_can_release(self):
		self.lock.release()
		self.assertFalse(self.lock.is_present())

##
##
class StopWatchTest(TestCase):

	def test_watch_001_can_read_elapsed_time(self):
		self.assertEqual('0:00:00.00' , str(StopWatch().elapsed())[:10])
