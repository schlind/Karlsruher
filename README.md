# Karlsruher Retweet Bot
!?!?!? [karlsruher.md](karlsruher.md)

## Executor's summary

	`# ./run.py`

## Abstract
A Karlsruher Retweet Bot is a robot on Twitter that reads and retweets tweets that mention it's name.

## Technology
* [Python](https://www.python.org/),
* [Tweepy](https://www.tweepy.org/) as Twitter client
* [SQLite](https://www.sqlite.org/) as database

*Disclaimer: It's my first Python project, feedback welcome!*

## Essential files

### credentials.py.example & credentials.py
Must contain valid tokens for the connected Twitter account.
[API-Keys](https://developer.twitter.com)

	`# cp credentials.py.example credentials.py`

### karlsruher.py
Module library, classes only.

#### class Karlsruher & KarlsruherTest
Retweet Bot implementation and tests.

#### class Brain & BrainTest
Persistence implementation and tests.

#### class Twitter
Twitter API as required, can be mocked for tests.

#### class CommandLine
Command line interface to run the bot.

#### Internal auxiliary classes, separation of concerns
* StopWatch to measure runtime
* Lock + LockTest to implement file based locks
* SelfTest to provide and run the TestSuite


### run.py
Runs the bot.

	`# run.py`

### Runtime, Database & lock files
Depending on the bot's name:
* HOME/*botname*.db - SQlite3 database file, bot's brain
* HOME/.lock.*botname* - locks new executions while an instance is running
