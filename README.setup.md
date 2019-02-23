# Karlsruher Retweet Robot
## Setup
Install into Python 3 library:
```
pip3 install -U --user --pre karlsruher
```
The Bot needs:
* a *HOME* directory for database and lock files:
```
mkdir -p $HOME/karlsruher
```
* [Twitter API credentials](https://developer.twitter.com) in file *$HOME/karlsruher/credentials.py*:
```
echo >$HOME/karlsruher/credentials.py
echo "TWITTER_CONSUMER_KEY = 'Your Twitter API Consumer Key'" >>$HOME/karlsruher/credentials.py
echo "TWITTER_CONSUMER_SECRET = 'Your Twitter API Consumer Secret'" >>$HOME/karlsruher/credentials.py
echo "TWITTER_ACCESS_KEY = 'Your Twitter API Access Key'" >>$HOME/karlsruher/credentials.py
echo "TWITTER_ACCESS_SECRET = 'Your Twitter API Access Secret'" >>$HOME/karlsruher/credentials.py
```
## Run
```
karlsruher --home=$HOME/karlsruher -help
```
