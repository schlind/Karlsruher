# MentionRetweeter Twitter Karlsruher
# https://github.com/schlind/Karlsruher
'''
Test api extension
'''

import contextlib, io, os, sys, tempfile
from unittest import mock, TestCase
from unittest.mock import patch

import tweepy
from karlsruher.tweepyx import tweepyx

@contextlib.contextmanager
def managed_io():
    stdout, stderr = sys.stdout, sys.stderr
    try:
        stdio = io.StringIO()
        sys.stdout, sys.stderr = stdio, stdio
        yield stdio
    finally:
        sys.stdout, sys.stderr = stdout, stderr

class TweepyXTest(TestCase):

    def setUp(self):
        self.yaml_file = tempfile.NamedTemporaryFile(delete=False)
        os.remove(self.yaml_file.name)
        self.assertFalse(os.path.exists(self.yaml_file.name))

    def tearDown(self):
        if os.path.exists(self.yaml_file.name):
            os.remove(self.yaml_file.name)

    def test_fail_missing_auth_yaml(self):
        '''Fail when auth.yaml is missing'''
        self.assertRaises(FileNotFoundError, tweepyx.API, '/does/_not_/exist', False)

    def test_fail_broken_auth_yaml(self):
        '''Fail when auth.yaml is missing'''
        with open(self.yaml_file.name, 'w') as f:
            f.write('''broken
              yaml''')
        self.assertRaises(tweepy.error.TweepError, tweepyx.API, self.yaml_file.name, False)

    @patch('builtins.input', mock.Mock(side_effect=['A','B','C','D']))
    def test_can_ask(self):
        '''Ask correct tupel'''
        with managed_io() as (stdio):
            self.assertEqual(('A', 'B', 'C', 'D'), tweepyx.ask())

    @patch('builtins.input', mock.Mock(side_effect=['A','B','C','D']))
    def test_can_create_auth_yaml(self):
        '''Auth file created'''
        with managed_io() as (stdio):
            tweepyx.create_auth_yaml_on_demand(self.yaml_file.name)
        self.assertTrue(os.path.exists(self.yaml_file.name))
        with open(self.yaml_file.name, 'r') as f:
            self.assertEqual([
                'twitter:\n',
                '    consumer:\n',
                "        key: 'A'\n",
                "        secret: 'B'\n",
                '    access:\n',
                "        key: 'C'\n",
                "        secret: 'D'"
        ], f.readlines())

    def test_not_overwriting_auth_yaml(self):
        '''Auth file not overwritten'''
        with open(self.yaml_file.name, 'w') as f:
            f.write('original')
        tweepyx.create_auth_yaml_on_demand(self.yaml_file.name)
        with open(self.yaml_file.name, 'r') as f:
            self.assertEqual(['original'], f.readlines())

    @patch('builtins.input', mock.Mock(side_effect=['A','B','C','D']))
    def test345(self):
        '''Get API instance'''
        with managed_io() as (stdio):
            self.assertTrue(tweepyx.API(auth_yaml=self.yaml_file.name, create_on_demand=True) is not None)

    @patch('builtins.input', mock.Mock(side_effect=['consumerkey','consumersecret','pin']))
    @patch('tweepy.OAuthHandler', mock.Mock())
    def test_syn2(self):
        '''Tribute syn2'''
        with managed_io() as (stdio):
            tweepyx.syn2()
        console = stdio.getvalue()
        self.assertTrue('Please authorize: ' in console)
        self.assertTrue('Access Key: ' in console)
        self.assertTrue('Access Secret: ' in console)
