# Karlsruher Retweet Bot
!?!?!? [karlsruher.md](karlsruher.md)

## Executor's summary

	`# python3 -m karlsruher`

## Abstract
A Karlsruher Retweet Bot is a robot on Twitter that reads and retweets tweets that mention it's name.

## Technology
* [Python](https://www.python.org/),
* [Tweepy](https://www.tweepy.org/) as Twitter client
* [SQLite](https://www.sqlite.org/) as database

*Disclaimer: It's my first Python project, feedback welcome!*


## Run

	`python3 -m karlsruher`

	`python3 -m unittest -v`

	`python3 -m pytest tests --cov=karlsruher --cov-report=html --cov-branch`


### Runtime, Database & lock files
Depending on the bot's name:
* HOME/*botname*.db - SQlite3 database file, bot's brain
* HOME/.lock.*botname* - locks new executions while an instance is running
