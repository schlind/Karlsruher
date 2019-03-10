# Karlsruher Retweet Robot
# https://github.com/schlind/Karlsruher

"""Main function"""

import logging
import sys
import karlsruher


def main():
    """Setup logging and run the commandline.

    :return: The exit-code of the commandline
    :rtype: int
    """

    logging.basicConfig(
        level=logging.DEBUG if '-debug' in sys.argv else logging.INFO,
        format='%(asctime)s %(levelname)-5.5s [%(name)s.%(funcName)s]: %(message)s',
        handlers=[logging.StreamHandler()]
    )

    return karlsruher.CommandLine.run()


if __name__ == '__main__':
    exit(main())
