'''
KarlsruherException LockException Lock StopWatch
'''

from datetime import datetime
import os
import logging

class KarlsruherException(Exception):
    '''Indicate an error within the karlsruher package'''

class LockException(KarlsruherException):
    '''Indicate/enforce a lock'''

class Lock:
    '''Provide file-based locking'''

    def __init__(self, path):
        ''':param path: The path for the lock file'''
        self.path = path
        self.logger = logging.getLogger(__class__.__name__)

    def __repr__(self):
        ''':return: The Lock as string '''
        return 'Lock is {}.'.format(
            'acquired' if os.path.isfile(self.path) else 'free')

    def is_acquired(self):
        ''':return: True if the lock is acquired, otherwise False'''
        self.logger.debug(self)
        return os.path.isfile(self.path)

    def acquire(self,log_message=None):
        ''':raises: LockException when the lock is already acquired'''
        if self.is_acquired():
            raise LockException('Locked by "{}".'.format(self.path))
        open(self.path, 'w').close()
        self.logger.debug(self)
        if log_message:
            self.logger.info(log_message)

    def release(self,log_message=None):
        '''Release the lock, remove the lock file'''
        if self.is_acquired():
            os.remove(self.path)
        self.logger.debug(self)
        if log_message:
            self.logger.info(log_message)

class StopWatch:
    '''Provide runtime measurement'''

    def __init__(self):
        '''Create an instance with start time now'''
        self.start = datetime.now()

    def elapsed(self):
        ''':return: The elapsed time since creation as string'''
        return str(datetime.now() - self.start)
