# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher
"""
Test tweepy extension
"""

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
        """Fail when auth.yaml is missing."""
        self.assertRaises(Exception, tweepyx.API, '/does/_not_/exist', False)

    @patch('builtins.input', mock.Mock(side_effect=['A','B','C','D']))
    def test_can_ask(self):
        """Ask creates the correct tupel."""
        self.assertEqual(('A', 'B', 'C', 'D'), tweepyx.ask())

    @patch('builtins.input', mock.Mock(side_effect=['A','B','C','D']))
    def test_can_create_auth_yaml(self):
        """Auth file created."""
        with managed_io() as (stdio):
            tweepyx.create_auth_yaml(self.yaml_file.name)
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

    @patch('builtins.input', mock.Mock(side_effect=['A','B','C','D']))
    def test345(self):
        """Provider must fail with invalid yaml."""
        with managed_io() as (stdio):
            self.assertTrue(tweepyx.API(auth_yaml=self.yaml_file.name) is not None)
