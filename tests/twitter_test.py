# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher
"""
Test ApiProvider and Twitter
"""

import tempfile
from unittest import mock, TestCase

from karlsruher.common import KarlsruhError
from karlsruher.twitter import Twitter
from karlsruher.tweepyx import tweepyx

class TwitterTest(TestCase):

    def test_can_reach_connected_state(self):
        """Twitter must be connected."""
        auth_yaml = tempfile.NamedTemporaryFile(delete=False)
        auth_yaml.write(tweepyx.YAML_EXAMPLE.encode())
        auth_yaml.close()
        self.assertRaises(KarlsruhError, Twitter, auth_yaml.name)
