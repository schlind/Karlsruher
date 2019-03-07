"""
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher
"""

import tempfile
from unittest import mock, TestCase

import karlsruher


class CredentialsTest(TestCase):

    def test_can_read_credentials(self):
        yaml_file = tempfile.NamedTemporaryFile(delete=False)
        yaml_file.write(karlsruher.Credentials.__doc__.encode())
        yaml_file.close()
        credentials = karlsruher.Credentials(yaml_file.name)
        self.assertEqual('YOUR-CONSUMER-KEY', credentials.consumer_key)
        self.assertEqual('YOUR-CONSUMER-SECRET', credentials.consumer_secret)
        self.assertEqual('YOUR-ACCESS-KEY', credentials.access_key)
        self.assertEqual('YOUR-ACCESS-SECRET', credentials.access_secret)

    def test_can_fail_credentials(self):
        self.assertRaises(
            karlsruher.twitter.CredentialsException,
            karlsruher.Credentials, ''
        )

    def test_can_fail_unplausible_credentials(self):

        probes = [
"""
twitter:
    consumer:
        secret: 'BAR'
    access:
        key: 'FOO'
        secret: 'BAR'
""",
"""
twitter:
    consumer:
        key: 'FOO'
    access:
        key: 'FOO'
        secret: 'BAR'
""",
"""
twitter:
    consumer:
        key: 'FOO'
        secret: 'BAR'
    access:
        secret: 'BAR'
""",
"""
    consumer:
        key: 'FOO'
        secret: 'BAR'
    access:
        key: 'FOO'
""",
"""
twitter: ~
""",
'',

        ]

        for probe in probes:
            with self.subTest(probe=probe):
                yaml_file = tempfile.NamedTemporaryFile(delete=False)
                yaml_file.write(probe.encode())
                yaml_file.close()
                self.assertRaises(
                    karlsruher.twitter.CredentialsException,
                    karlsruher.Credentials, yaml_file.name
                )


class TwitterTest(TestCase):

    @mock.patch('tweepy.API', autospec=True)
    def test_can_read_credentials(self, tweepy_mock):
        yaml_file = tempfile.NamedTemporaryFile(delete=False)
        yaml_file.write(karlsruher.Credentials.__doc__.encode())
        yaml_file.close()
        karlsruher.karlsruher.Twitter(yaml_file.name)
        self.assertEqual(1, tweepy_mock.call_count)
