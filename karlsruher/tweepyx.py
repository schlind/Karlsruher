# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher
"""
Convenience extension for tweepy.API creation
"""

import os
import tweepy
import yaml

# pylint: disable=invalid-name
class tweepyx:
    """
    Feature YAML file base authentication
    """

    YAML_TEMPLATE = '''
twitter:
    consumer:
        key: '{0}'
        secret: '{1}'
    access:
        key: '{2}'
        secret: '{3}'
    '''.strip()


    YAML_EXAMPLE = YAML_TEMPLATE.format(
        'YOUR-CONSUMER-KEY', 'YOUR-CONSUMER-SECRET',
        'YOUR-ACCESS-KEY', 'YOUR-ACCESS-SECRET'
    )


    @staticmethod
    def API(auth_yaml, create_file=True):
        """
        :return: The authenticated tweepy.API
        """
        if create_file:
            tweepyx.create_auth_yaml(auth_yaml)
        if not os.path.isfile(auth_yaml):
            raise FileNotFoundError(
                'Please create file "{}" with contents:\n{}'.format(
                    auth_yaml, tweepyx.YAML_TEMPLATE
                )
            )
        with open(auth_yaml, 'r') as yaml_file:
            try:
                read_yaml = yaml.load(yaml_file)
                credentials = (
                    read_yaml['twitter']['consumer']['key'],
                    read_yaml['twitter']['consumer']['secret'],
                    read_yaml['twitter']['access']['key'],
                    read_yaml['twitter']['access']['secret']
                )
            except:
                raise tweepy.TweepError(
                    'Please check file "{}" for proper contents:\n{}'.format(
                        auth_yaml, tweepyx.YAML_EXAMPLE
                    )
                )
        consumer_key, consumer_secret, access_key, access_secret = credentials
        oauth_handler = tweepy.OAuthHandler(consumer_key, consumer_secret)
        oauth_handler.set_access_token(access_key, access_secret)
        return tweepy.API(
            auth_handler=oauth_handler,
            compression=True,
            wait_on_rate_limit=True,
            wait_on_rate_limit_notify=True
        )

    @staticmethod
    def ask():
        """
        :return: The credentials given by the user
        """
        print('Your Twitter API credentials:')
        return (
            input('CONSUMER KEY? ').strip(),
            input('CONSUMER SECRET? ').strip(),
            input('ACCESS KEY? ').strip(),
            input('ACCESS SECRET? ').strip()
        )

    @staticmethod
    def create_auth_yaml(auth_yaml_file):
        """
        :param auth_yaml_file: The file to create
        """
        if os.path.isfile(auth_yaml_file):
            return
        consumer_key, consumer_secret, access_key, access_secret = tweepyx.ask()
        yaml_content = tweepyx.YAML_TEMPLATE.format(
            consumer_key, consumer_secret, access_key, access_secret
        ).strip()
        print('Creating file', auth_yaml_file, 'with content:\n', yaml_content)
        with open(auth_yaml_file, 'w') as yaml_file:
            yaml_file.write(str(yaml_content))

    @staticmethod
    def syn2():
        """
        Replaces "authorize_access_token.py" and "register.py"...
        :return:
        """
        consumer_key = input('Consumer Key: ').strip()
        consumer_secret = input('Consumer Secret: ').strip()
        oauthhandler = tweepy.OAuthHandler(consumer_key, consumer_secret)
        authorization_url = oauthhandler.get_authorization_url()
        print('Please authorize:', authorization_url)
        verifier = input('Enter PIN: ').strip()
        oauthhandler.get_access_token(verifier)
        print("Access Key:    '%s'" % oauthhandler.access_token.key)
        print("Access Secret: '%s'" % oauthhandler.access_token.secret)
