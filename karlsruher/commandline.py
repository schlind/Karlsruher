'''
Commandline
'''

import sys

from .karlsruher import Karlsruher
from .__version__ import __version__


TEXT_HELP = '''

Karlsruher Twitter Robot v{}

Retweet followers with:
    
    $ karlsruher --home=/PATH [-noact] [-debug]


Do housekeeping with:

    $ karlsruher --home=/PATH -housekeeping [-debug]


Required argument:

    --home=PATH     specify a home directory


Other optional options:

    -noact          do internal stuff but do not act on Twitter
    -version        print version information and exit
    -help           you are reading this right now
    -debug          sets console logging to DEBUG


Example Cronjobs:

# Cronjob for retweets runs every 5 minutes:
*/5 * * * * karlsruher --home=/PATH >/dev/null 2>&1
# Cronjob for housekeeping runs once per day:
3 3 * * * karlsruher --home=/PATH -housekeeping >/dev/null 2>&1


Cheers!
'''.strip().format(__version__)

TEXT_PLEASE_SPECIFY_HOME = 'Please specify a home directory with "--home=/PATH".'

class CommandLine:
    '''Commandline interface'''

    @staticmethod
    def run():
        ''':return: Shell exit code 1 in case of any error, otherwise 0'''

        if '-help' in sys.argv:
            print(TEXT_HELP)
            return 0

        if '-version' in sys.argv:
            print(TEXT_HELP.splitlines()[0])
            return 0

        # Find home directory in arguments:
        home = None
        for arg in sys.argv:
            if not home and arg.startswith('--home='):
                home = arg[len('--home='):]

        # Help user:
        if not home:
            print(TEXT_HELP)
            print(TEXT_PLEASE_SPECIFY_HOME)
            return 1

        try:

            # Configure and run:
            bot = Karlsruher(home)
            if '-noact' in sys.argv:
                bot.act_on_twitter = False
            if '-housekeeping' in sys.argv:
                bot.housekeeping()
            bot.feature_retweets()
            return 0

        # pylint: disable=broad-except
        # Excuse: The user should see whatever exception arrives here
        except Exception as error_message:
            print(error_message)
            return 1
