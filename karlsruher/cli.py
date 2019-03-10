# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher
"""
The commandline to run all the robots
"""

import sys

from .housekeeping import HouseKeeper
from .karlsruher import Karlsruher
from .robot import Config
from .version import __version__


HELP_TEXT = """

Karlsruher Twitter Robot v{}

Example Usage:
    karlsruher --home=/PATH [-read [-retweet] [-reply]|-talk|-housekeeping] [-debug]

Options
    -version    print version information and exit
    -help       you are reading this right now

Arguments:

    --home=PATH specify a home directory

    -read       read mention timeline
    -retweet    enable the retweet feature
    -reply      publicly reply on some tweets
    -talk       combines all of -read, -retweet, -reply


    -housekeeping	Perform housekeeping tasks and exit.
        This fetches followers and friends from Twitter.
        Due to API Rate Limits, housekeeping is throttled
        and takes up to 1 hour per 1000 followers/friends.
        Run this nightly once per day.

    -debug  sets console logging from INFO to DEBUG

Cronjobs:

# Cronjob reading mentions, should run every 5 minutes:
*/5 * * * * karlsruher --home=/PATH -talk >/dev/null 2>&1

# Cronjob for housekeeping, should run once per day, nightly:
3 3 * * * karlsruher --home=/PATH -housekeeping >/dev/null 2>&1


Cheers!
""".strip().format(__version__)


class CommandLine:
    """
    Provide a commandline interface.
    """

    @staticmethod
    def run():
        """
        Read command line arguments and behave accordingly.
        :return: Shell exit code 1 in case of any error, otherwise 0
        """
        if '-version' in sys.argv:
            print(HELP_TEXT.splitlines()[0])
            return 0

        home, task = None, None
        for arg in sys.argv:
            if not home and arg.startswith('--home='):
                home = arg[len('--home='):]
            if not task and arg in ['-housekeeping', '-read', '-talk']:
                task = arg

        if not task or '-help' in sys.argv:
            print(HELP_TEXT)
            return 0

        if not home:
            print('Please specify a home directory with "--home=/PATH".')
            return 1

        try:
            config = Config(
                home=home,
                do_reply='-reply' in sys.argv or '-talk' in sys.argv,
                do_retweet='-retweet' in sys.argv or '-talk' in sys.argv
            )
            if task == '-housekeeping':
                HouseKeeper(config).perform()
            elif task in ['-read', '-talk']:
                Karlsruher(config).perform()
            return 0
        # pylint: disable=broad-except
        # because the user should see whatever exception arrives here.
        except Exception as error_message:
            print(error_message)
            return 1
