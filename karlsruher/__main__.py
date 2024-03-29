'''
Main function, logging configuration, run application
'''

import logging
import sys

from karlsruher import Karlsruher
from karlsruher import CONSOLE_HELP_TEXT
from karlsruher import read_mentions
from karlsruher import retweet_mentions
from karlsruher import delete_aged_tweets
from karlsruher import rhein


# pylint: disable=too-many-branches
def main():
    '''
    Main function.
    '''
    if '-debug' in sys.argv:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)-5.5s [%(name)s.%(funcName)s]: %(message)s',
            handlers=[logging.StreamHandler()]
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(funcName)s]: %(message)s',
            handlers=[logging.StreamHandler()]
        )

    if len(sys.argv) == 1 or '-help' in sys.argv:
        print(CONSOLE_HELP_TEXT)
        return 0

    if '-version' in sys.argv:
        print(CONSOLE_HELP_TEXT.splitlines()[0])
        return 0

    try:
        karlsruher = Karlsruher()

        if '-housekeeping' in sys.argv:
            karlsruher.housekeeping()
        if '-wakeup' in sys.argv:
            karlsruher.wake_up('console')
        if '-sleep' in sys.argv:
            karlsruher.go_sleep('console')
        if '-read' in sys.argv:
            read_mentions(karlsruher)
        if '-retweet' in sys.argv:
            retweet_mentions(karlsruher)
        if '-forget' in sys.argv:
            delete_aged_tweets(karlsruher)
        if '-rhein' in sys.argv:
            rhein(karlsruher)

        return 0

    except NotADirectoryError as not_a_dir_error:
        print(not_a_dir_error)
        return 1
    except RuntimeError as runtime_error:
        print(runtime_error)
        return 1


if __name__ == '__main__':
    sys.exit(main())
