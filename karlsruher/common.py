"""
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher

Common auxiliary classes

"""


from datetime import datetime
import os


class StopWatch:

    """Provide runtime measurement."""

    def __init__(self):
        """Set the starting time to now."""
        self.start = datetime.now()

    def elapsed(self):
        """Return the elapsed time datetime object as string."""
        return str(datetime.now() - self.start)


class LockException(Exception):

    """Indicate a lock."""


class Lock:

    """Provide file-based locking."""

    def __init__(self, path):
        """Use the given path as lock-file."""
        self.path = path

    def is_present(self):
        """Indicate whether the lock is present or not."""
        return os.path.isfile(self.path)

    def acquire(self):
        """Try to acquire the lock.
        Raises LockException when the lock is already locked.
        """
        if self.is_present():
            raise LockException('Locked by "{}".'.format(self.path))
        open(self.path, 'a').close()

    def release(self):
        """Release the lock."""
        if self.is_present():
            os.remove(self.path)
