'''
CommandLineTest
'''

import contextlib
import io
import os
import sys
import tempfile
from unittest import mock
from unittest import TestCase

from karlsruher.commandline import CommandLine, TEXT_HELP, TEXT_PLEASE_SPECIFY_HOME

class CommandLineTest(TestCase):
    '''Test the CommandLine'''

    def setUp(self):
        '''Temporary home directory, dummy auth.yaml file, in-memory Brain'''
        self.test_home = tempfile.gettempdir()
        self.test_auth_yaml_file = '{}/auth.yaml'.format(self.test_home)
        self.test_brain_file = ':memory:'

    def tearDown(self):
        '''Remove dummy auth.yaml file'''
        if os.path.exists(self.test_auth_yaml_file):
            os.remove(self.test_auth_yaml_file)

    @contextlib.contextmanager
    def managed_io(self):
        '''Capture console'''
        stdout, stderr = sys.stdout, sys.stderr
        try:
            sys.stdout, sys.stderr = io.StringIO(), io.StringIO()
            yield sys.stdout, sys.stderr
        finally:
            sys.stdout, sys.stderr = stdout, stderr

    def test_can_show_version(self):
        '''CommandLine must show a version on demand'''
        with self.managed_io() as (out, err):
            sys.argv = ['-version']
            self.assertEqual(0, CommandLine.run())
            console = out.getvalue().strip()
            self.assertEqual(TEXT_HELP.splitlines()[0], console)

    def test_can_show_help(self):
        '''CommandLine must show help on demand'''
        with self.managed_io() as (out, err):
            sys.argv = ['-help']
            self.assertEqual(0, CommandLine.run())
            console = out.getvalue().strip()
            self.assertEqual(TEXT_HELP, console)

    def test_can_show_help_without_home(self):
        '''CommandLine must show help'''
        with self.managed_io() as (out, err):
            sys.argv = ['']
            self.assertEqual(1, CommandLine.run())
            console = out.getvalue().strip()
            self.assertEqual(TEXT_HELP + '\n' + TEXT_PLEASE_SPECIFY_HOME, console)

    def test_can_show_error_non_existing_home(self):
        '''CommandLine must show error with non existing home'''
        with self.managed_io() as (out, err):
            sys.argv = ['--home=/does/not/exist']
            self.assertEqual(1, CommandLine.run())
            console = out.getvalue().strip()
            self.assertTrue(console.startswith('Specified home '))
            self.assertEqual(' not found.', console[len(console)-len(' not found.'):])

    def test_can_run_until_credentials_missing(self):
        '''CommandLine must show error when credentials missing'''
        with self.managed_io() as (out, err):
            sys.argv = ['--home={}'.format(self.test_home)]
            self.assertEqual(1, CommandLine.run())
            console = out.getvalue().strip()
            self.assertTrue(console.startswith('Please create file "'), console)
            self.assertTrue('/auth.yaml' in console)

    @mock.patch('karlsruher.tweepyx.API', mock.MagicMock())
    @mock.patch('karlsruher.twitter.Twitter.me', mock.MagicMock(return_value=mock.Mock(id=0,screen_name='TestBot')))
    @mock.patch('karlsruher.twitter.Twitter.follower_ids', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.friend_ids', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.list_members', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.mentions_timeline', mock.MagicMock(return_value=[]))
    def test_can_run(self):
        '''CommandLine must run silently with --home'''
        with self.managed_io() as (out, err):
            sys.argv = ['--home={}'.format(self.test_home)]
            exit_code = CommandLine.run()
            console = out.getvalue().strip()
            self.assertEqual('', console)
            self.assertEqual(0, exit_code)

    @mock.patch('karlsruher.tweepyx.API', mock.MagicMock())
    @mock.patch('karlsruher.twitter.Twitter.me', mock.MagicMock(return_value=mock.Mock(id=0,screen_name='TestBot')))
    @mock.patch('karlsruher.twitter.Twitter.follower_ids', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.friend_ids', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.list_members', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.mentions_timeline', mock.MagicMock(return_value=[]))
    def test_can_run_housekeeping(self):
        '''CommandLine must run silently with -nousekeeping'''
        with self.managed_io() as (out, err):
            sys.argv = ['--home={}'.format(self.test_home), '-housekeeping']
            exit_code = CommandLine.run()
            console = out.getvalue().strip()
            self.assertEqual('', console)
            self.assertEqual(0, exit_code)

    @mock.patch('karlsruher.tweepyx.API', mock.MagicMock())
    @mock.patch('karlsruher.twitter.Twitter.me', mock.MagicMock(return_value=mock.Mock(id=0,screen_name='TestBot')))
    @mock.patch('karlsruher.twitter.Twitter.follower_ids', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.friend_ids', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.list_members', mock.MagicMock(return_value=[]))
    @mock.patch('karlsruher.twitter.Twitter.mentions_timeline', mock.MagicMock(return_value=[]))
    def test_can_run_without_acting(self):
        '''CommandLine must run silently with -noact'''
        with self.managed_io() as (out, err):
            sys.argv = ['--home={}'.format(self.test_home), '-noact']
            exit_code = CommandLine.run()
            console = out.getvalue().strip()
            self.assertEqual('', console)
            self.assertEqual(0, exit_code)
