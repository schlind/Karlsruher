'''
TwitterTest
'''

import tempfile
from unittest import mock, TestCase
from unittest.mock import patch

from karlsruher.twitter import Twitter
from karlsruher.tweepyx import tweepyx

class TwitterTest(TestCase):

    def test_can_fail(self):
        '''Must do nothing without auth.yaml file'''
        self.assertRaises(Exception, Twitter)
        self.assertRaises(Exception, Twitter, '/should/_not_/exist')

    @patch('tweepy.API.me', mock.Mock(return_value=mock.Mock(id=1, screen_name='test')))
    def test_can_reach_connected_state(self):
        '''Must connect to Twitter'''
        auth_yaml = tempfile.NamedTemporaryFile(delete=False)
        auth_yaml.write(tweepyx.YAML_EXAMPLE.encode())
        auth_yaml.close()
        twitter = Twitter(auth_yaml.name)
        self.assertEqual('test', twitter.screen_name)
