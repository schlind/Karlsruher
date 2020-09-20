'''
BrainTest
'''

from unittest import TestCase
from karlsruher.brain import Brain

class BrainTest(TestCase):
    '''Test the Brain'''

    def setUp(self):
        '''Use an in-memory database'''
        self.brain = Brain(':memory:')

    def test_can_store_and_find_users(self):
        '''Brain must be able to add, import  and find users'''
        self.assertFalse(self.brain.find_user('testuser', 123))
        self.assertEqual(1, self.brain.store_user('testuser', 123))
        self.assertTrue(self.brain.find_user('testuser', 123))

    def test_can_import_users(self):
        '''Brain must import users'''
        self.assertEqual(1, self.brain.store_user('testuser', 123))
        self.brain.import_users('testuser', lambda: [456, 789])
        self.assertFalse(self.brain.find_user('testuser', 123))
        self.assertTrue(self.brain.find_user('testuser', 456))
        self.assertTrue(self.brain.find_user('testuser', 789))

    def test_can_store_and_find_tweets(self):
        '''Brain must provide tweets'''
        self.assertFalse(self.brain.find_tweet(123))
        self.assertEqual(1, self.brain.store_tweet(123))
        self.assertTrue(self.brain.find_tweet(123))

    def test_metrics_present(self):
        '''Brain must provide metrics'''
        metrics = str(self.brain)
        self.assertTrue('0 tweets' in metrics)
        self.assertTrue('0 users' in metrics)
