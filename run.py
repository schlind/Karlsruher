#!/usr/bin/env python3
## Karlsruher Retweet Bot https://github.com/schlind/Karlsruher
from sys import version_info as python_version
assert python_version >= (3,)
from os import path as fs
from sys import argv
from karlsruher import CommandLine
CommandLine.run(fs.dirname(fs.realpath(__file__)), argv)
