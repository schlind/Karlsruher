# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher

"""
"""

import contextlib
import io
import os
import sys
import tempfile
from unittest import mock
from unittest import TestCase

from karlsruher.cli import CommandLine

class CommandLineTest(TestCase):

    known_task_args = ['-housekeeping', '-read', '-talk']

    def setUp(self):
        self.test_home = tempfile.gettempdir()
        self.test_auth_yaml_file = '{}/auth.yaml'.format(self.test_home)

    def tearDown(self):
        if os.path.exists(self.test_auth_yaml_file):
            os.remove(self.test_auth_yaml_file)

    @contextlib.contextmanager
    def managed_io(self):
        stdout, stderr = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
            yield sys.stdout, sys.stderr
        finally:
            sys.stdout, sys.stderr = stdout, stderr

    def test_can_show_version(self):
        with self.managed_io() as (out, err):
            sys.argv = ['-version']
            self.assertEqual(0, CommandLine.run())
            console = out.getvalue().strip()
            self.assertTrue(console.startswith('Karlsruher '), console)

    def test_can_show_help(self):
        with self.managed_io() as (out, err):
            for arg in ['', '-help', 'what?']:
                sys.argv = [arg]
                self.assertEqual(0, CommandLine.run())
                console = out.getvalue().strip()
                self.assertTrue(console.startswith('Karlsruher '), console)

    def test_can_show_error_missing_home(self):
        with self.managed_io() as (out, err):
            for arg in self.known_task_args:
                sys.argv = [arg]
                self.assertEqual(1, CommandLine.run())
                console = out.getvalue().strip()
                self.assertTrue(console.startswith('Please specify '), console)

    def test_can_show_error_non_existing_home(self):
        with self.managed_io() as (out, err):
            for arg in self.known_task_args:
                sys.argv = [arg, '--home=/does/not/exist']
                self.assertEqual(1, CommandLine.run())
                console = out.getvalue().strip()
                self.assertTrue(console.startswith('Specified home '), console)

    def test_can_run_until_credentials_missing(self):
        with self.managed_io() as (out, err):
            for arg in self.known_task_args:
                sys.argv = [arg, '--home={}'.format(self.test_home)]
                self.assertEqual(1, CommandLine.run())
                console = out.getvalue().strip()
                self.assertTrue(console.startswith('Please create '), console)

    @mock.patch('karlsruher.twitter.ApiProvider',
        mock.Mock(api=mock.MagicMock(return_value=mock.Mock()))
    )
    @mock.patch('karlsruher.twitter.Twitter.me', mock.MagicMock(return_value=mock.Mock(id=0,screen_name='test')))
    @mock.patch('karlsruher.twitter.Twitter.followers', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.friends', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.list_members', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.mentions_timeline', mock.MagicMock(return_value=[]))
    def test_can_run(self):
        with self.managed_io() as (out, err):
            for arg in self.known_task_args:
                sys.argv = [arg, '--home={}'.format(self.test_home)]
                exit_code = CommandLine.run()
                console = out.getvalue().strip()
                self.assertEqual('', console)
                self.assertEqual(0, exit_code)
                self.assertEqual(0, len(console))
