## Karlsruher Retweet Bot
## https://github.com/schlind/Karlsruher

from datetime import datetime
import os


##
##
class StopWatch:

    def __init__(self):
        self.start = datetime.now()

    def elapsed(self):
        return datetime.now() - self.start


##
##
class Lock:

    def __init__(self, path):
        self.path = path

    def is_present(self):
        return os.path.isfile(self.path)

    def acquire(self):
        if self.is_present():
            return False
        open(self.path, 'a').close()
        return self.is_present()

    def release(self):
        if self.is_present():
            os.remove(self.path)
