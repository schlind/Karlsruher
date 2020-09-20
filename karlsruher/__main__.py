'''
Main function, logging configuration, run application
'''

import logging
import sys

import karlsruher

def main():
    '''
    :return: The exit-code of the commandline
    :rtype: int
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
    return karlsruher.CommandLine.run()


if __name__ == '__main__':
    sys.exit(main())
