'''
Main function, logging configuration, run application
'''

import logging
import sys

from karlsruher import Karlsruher
from karlsruher import CONSOLE_HELP_TEXT
from karlsruher import read_mentions
from karlsruher import retweet_mentions



if __name__ == '__main__':

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
        sys.exit(0)

    if '-version' in sys.argv:
        print(CONSOLE_HELP_TEXT.splitlines()[0])
        sys.exit(0)

    karlsruher = Karlsruher()

    if '-read' in sys.argv:
        read_mentions(karlsruher)

    if '-retweet' in sys.argv:
        retweet_mentions(karlsruher)

    sys.exit(0)
