# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher

"""
"""

import tempfile
from unittest import mock, TestCase

from karlsruher.twitter import ApiProvider, TwittError, Twitter

class ApiProviderTest(TestCase):

    def test_can_fail_no_auth_file(self):
        """Provider must fail without credentials file."""
        provider = ApiProvider(None)
        self.assertRaises(TwittError, provider.read_credentials)

    def test_can_fail_auth_file_not_present(self):
        """Provider must fail without credentials file."""
        provider = ApiProvider('./not/existing/file')
        self.assertRaises(FileNotFoundError, provider.read_credentials)

    def test_can_read_credentials(self):
        """Provider must read credentials correctly."""
        yaml_file = tempfile.NamedTemporaryFile(delete=False)
        yaml_file.write(ApiProvider.yaml_content.encode())
        yaml_file.close()
        consumer_key, consumer_secret, access_key, access_secret = ApiProvider(yaml_file.name).read_credentials()
        self.assertEqual('YOUR-CONSUMER-KEY', consumer_key)
        self.assertEqual('YOUR-CONSUMER-SECRET', consumer_secret)
        self.assertEqual('YOUR-ACCESS-KEY', access_key)
        self.assertEqual('YOUR-ACCESS-SECRET', access_secret)

    def test_can_get_oauthhandler(self):
        """Provider must provide oauth_handler."""
        yaml_file = tempfile.NamedTemporaryFile(delete=False)
        yaml_file.write(ApiProvider.yaml_content.encode())
        yaml_file.close()
        o = ApiProvider(yaml_file.name).oauth_handler()

    def test_can_fail_unplausible_credentials(self):
        """Provider must fail with invalid yaml."""
        yaml_file = tempfile.NamedTemporaryFile(delete=False)
        yaml_file.write("""
            invalid 
                yaml.
        """.encode())
        yaml_file.close()
        provider = ApiProvider(yaml_file.name)
        self.assertRaises(TwittError, provider.read_credentials)


class TwitterTest(TestCase):

    @mock.patch('karlsruher.twitter.ApiProvider.api', mock.Mock())
    @mock.patch('karlsruher.twitter.Twitter.me', mock.MagicMock(return_value=mock.Mock(id=0,screen_name='test')))
    def test_can_reach_connected_state(self):
        """Twitter must be connected."""
        yaml_file = tempfile.NamedTemporaryFile(delete=False)
        yaml_file.write(ApiProvider.yaml_content.encode())
        yaml_file.close()
        twitter = Twitter(yaml_file.name)
        self.assertEqual('test', twitter.screen_name)
