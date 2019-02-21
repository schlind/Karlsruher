'''
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher

Run it.

'''

import logging
import sys
from karlsruher import CommandLine

logging.basicConfig(
    level=logging.DEBUG if '-debug' in sys.argv else logging.INFO,
    format='%(asctime)s %(levelname)-5.5s [%(name)s.%(funcName)s]: %(message)s',
    handlers=[logging.StreamHandler()]
)


def main():
    '''__main__.main()'''
    exit(CommandLine.run())

if __name__ == '__main__':
    main()
