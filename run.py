#!/usr/bin/env python3
## https://github.com/schlind/Karlsruher
from os import path
from karlsruher import CommandLine
home = path.dirname(path.realpath(__file__))
CommandLine.run(home)
