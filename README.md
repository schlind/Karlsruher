# Karlsruher Retweet Robot
!?!?!? -> [karlsruher.md](https://github.com/schlind/Karlsruher/blob/master/karlsruher.md)


## Abstract
A Karlsruher Retweet Bot is a robot on Twitter that reads and retweets tweets that mention it's name.


## Technology
Hopefully clean-coded and self-explaining [Python](https://www.python.org/) using [Tweepy](https://www.tweepy.org/) as Twitter client and [SQLite](https://www.sqlite.org/) as database.


## Lifecycle
From source to command line help:

```
# checkout source
git clone https://github.com/schlind/Karlsruher.git
cd Karlsruher

# run tests and reports
python3 -m unittest tests -v
python3 -m pytest tests --cov=karlsruher --cov-report=html --cov-branch
python3 -m pylint karlsruher

# create source distribution artifact
python3 setup.py sdist

# install source distribution artifact
pip3 install --user dist/karlsruher-2.0b0.tar.gz

# remove cloned source
cd .. && rm -r Karlsruher

# execute installed module
python3 -m karlsruher

# execute installed binary
/path/to/bin/karlsruher
```


## Runtime
The Bot needs a *HOME* directory for it's credentials, database and lock files...

```
mkdir -p $HOME/karlsruher
```

... and some [Twitter API credentials](https://developer.twitter.com) in *$KARLSRUHER_HOME/credentials.py* as well...


```
echo >$HOME/karlsruher/credentials.py
echo "TWITTER_CONSUMER_KEY = 'Your Twitter API Consumer Key'" >>$HOME/karlsruher/credentials.py
echo "TWITTER_CONSUMER_SECRET = 'Your Twitter API Consumer Secret'" >>$HOME/karlsruher/credentials.py
echo "TWITTER_ACCESS_KEY = 'Your Twitter API Access Key'" >>$HOME/karlsruher/credentials.py
echo "TWITTER_ACCESS_SECRET = 'Your Twitter API Access Secret'" >>$HOME/karlsruher/credentials.py
```

... that's it, now run...

```
# configure and run by command line argument
/path/to/bin/karlsruher --home=$HOME/karlsruher -read

# configure and run by env var
KARLSRUHER_HOME=$HOME/karlsruher /path/to/bin/karlsruher -read
```


### Automagic
```
*/5 * * * * /path/to/bin/karlsruher --home=/PATH -talk >/dev/null 2>&1
3 3 * * * /path/to/bin/karlsruher --home=/PATH -housekeeping >/dev/null 2>&1
```
