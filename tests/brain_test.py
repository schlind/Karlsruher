'''
BrainTest
'''

from unittest import TestCase
from karlsruher.brain import Brain

class BrainTest(TestCase):
    '''
    Test the Brain
    '''

    def setUp(self):
        self.brain = Brain()

    def test_is_empty(self):
        '''Brain must be empty'''
        self.assertEqual('Having.', str(self.brain))
        self.assertFalse(self.brain.has(None, None))
        self.assertTrue(self.brain.get(None, None) is None)
        self.assertEqual(None, self.brain.get(None, None))

    def test_can_store_entries_and_data(self):
        '''Brain must store entries'''
        self.assertFalse(self.brain.has('test', 1))
        self.assertEqual(1, self.brain.store('test', 1))
        self.assertEqual(1, self.brain.store('test', 2, 'data'))
        self.assertTrue(self.brain.has('test', 1))
        self.assertTrue(self.brain.has('test', 2))
        self.assertEqual(None, self.brain.get('test', 1))
        self.assertEqual('data', self.brain.get('test', 2))

    def test_can_forget(self):
        '''Brain must forget one'''
        self.assertEqual(1, self.brain.store('test', 1))
        self.assertEqual(1, self.brain.store('test', 2))
        self.assertEqual(1, self.brain.store('test', 3))
        self.assertEqual(1, self.brain.store('test', 4))
        self.assertEqual(1, self.brain.forget('test', 3))
        self.assertFalse(self.brain.has('test', 3))
        self.assertEqual(3, self.brain.forget('test'))
