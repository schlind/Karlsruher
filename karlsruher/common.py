# Karlsruher Twitter Robot
# https://github.com/schlind/Karlsruher
"""
Common auxiliary classes
"""

from datetime import datetime
import os


class KarlsruhError(Exception):
    """
    Indicate an error within the karlsruher package.
    """


class StopWatch:
    """
    Provide runtime measurement.
    """

    def __init__(self):
        """
        Create instance starting now.
        """
        self.start = datetime.now()

    def elapsed(self):
        """
        :return: The elapsed time since creation as string.
        """
        return str(datetime.now() - self.start)


class Lock:
    """
    Provide file-based locking.
    """

    def __init__(self, path):
        """
        Use the given path as lock file.
        :param path: The path
        """
        self.path = path

    def is_acquired(self):
        """
        Indicate whether the lock is present or not.
        :return: True if the lock is acquired, otherwise False
        """
        return os.path.isfile(self.path)

    def acquire(self):
        """
        Try to acquire the lock, create the lock file.
        :raises: LockException when the lock is already acquired.
        """
        if self.is_acquired():
            raise LockException('Locked by "{}".'.format(self.path))
        open(self.path, 'w').close()

    def release(self):
        """
        Release the lock, remove the lock file.
        """
        if self.is_acquired():
            os.remove(self.path)


class LockException(KarlsruhError):
    """
    Indicate/enforce a lock.
    """
