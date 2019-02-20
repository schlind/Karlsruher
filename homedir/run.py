#!/usr/bin/env python3
## https://github.com/schlind/Karlsruher


## FIXME Rather realize to use "import karlsruher" instead
#import karlsruher
import os, sys
path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, path)
#print(sys.path)
import karlsruher
karlsruher.CommandLine.run()
