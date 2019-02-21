#!/usr/bin/env python3
## @Karlsruher Retweet Robot
## https://github.com/schlind/Karlsruher

import logging
import sys
import karlsruher

logging.basicConfig(
    level=logging.DEBUG if '-debug' in sys.argv else logging.INFO,
    format='%(asctime)s %(levelname)-5.5s [%(name)s.%(funcName)s]: %(message)s',
    handlers=[logging.StreamHandler()]
)

karlsruher.CommandLine.run()
