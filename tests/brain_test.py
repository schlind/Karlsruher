# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher

"""Test Brain"""

from unittest import mock
from unittest import TestCase


from karlsruher.brain import Brain

class BrainTest(TestCase):

    def setUp(self):
        self.brain = Brain(':memory:')
        self.user1 = mock.Mock(id=1, screen_name='user1')
        self.user2 = mock.Mock(id=2, screen_name='user2')
        self.user3 = mock.Mock(id=3, screen_name='user3')
        self.tweet1 = mock.Mock(id=111, user=self.user1)
        self.tweet2 = mock.Mock(id=222, user=self.user1)
        self.tweet3 = mock.Mock(id=333, user=self.user2)

    def test_can_get_default_value(self):
        self.assertEqual('default', self.brain.get('test', 'default'))

    def test_can_set_get_string_value(self):
        self.brain.set('test', 'string')
        self.assertEqual('string', self.brain.get('test'))

    def test_can_set_get_boolean_value_true(self):
        self.brain.set('test', True)
        self.assertTrue(self.brain.get('test'))

    def test_can_set_get_boolean_value_false(self):
        self.brain.set('test', False)
        self.assertFalse(self.brain.get('test'))

    def test_can_set_get_value_none_as_false(self):
        self.brain.set('test')
        self.assertIsNone(self.brain.get('test'))
        self.assertFalse(self.brain.get('test'))

    def test_can_add_and_have_followers(self):
        self.assertFalse(self.brain.has_follower(self.user3.id))
        self.assertEqual(1, self.brain.add_user('follower', self.user3))
        self.assertTrue(self.brain.has_follower(self.user3.id))

    def test_can_add_and_have_friends(self):
        self.assertFalse(self.brain.has_friend(self.user3.id))
        self.assertEqual(1, self.brain.add_user('friend', self.user3))
        self.assertTrue(self.brain.has_friend(self.user3.id))

    def test_can_import_followers(self):
        self.brain.import_followers(lambda: [self.user1, self.user2, self.user3])
        self.assertEqual(3, len(self.brain.users('follower')))

    def test_can_import_friends(self):
        self.brain.import_friends(lambda: [self.user1, self.user2, self.user3])
        self.assertEqual(3, len(self.brain.users('friend')))

    def test_can_count_tweets_empty(self):
        self.assertEqual(0, self.brain.count_tweets('test_type'))

    def test_can_add_and_have_tweet(self):
        self.assertFalse(self.brain.has_tweet('test_type', self.tweet1.id))
        self.assertEqual(1, self.brain.add_tweet('test_type', self.tweet1))
        self.assertTrue(self.brain.has_tweet('test_type', self.tweet1.id))

    def test_not_updating_tweets(self):
        self.assertFalse(self.brain.has_tweet('test_type', self.tweet1.id))
        self.assertEqual(1, self.brain.add_tweet('test_type', self.tweet1))
        self.assertEqual(0, self.brain.add_tweet('test_type', self.tweet1))

    def test_can_count_tweets(self):
        self.assertEqual(1, self.brain.add_tweet('test_type', self.tweet1))
        self.assertEqual(1, self.brain.add_tweet('test_type', self.tweet2))
        self.assertEqual(2, self.brain.count_tweets('test_type'))
        self.assertEqual(1, self.brain.add_tweet('test_type', self.tweet3))
        self.assertEqual(3, self.brain.count_tweets('test_type'))

    def test_metrics_present(self):
        metrics = self.brain.metrics()
        self.assertTrue('named values' in metrics)
        self.assertTrue('tweets' in metrics)
        self.assertTrue('followers' in metrics)
        self.assertTrue('friends' in metrics)
