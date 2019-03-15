# Karlsruher Twitter Robot
Karlsruher is a robot on Twitter that retweets followers who mention its name.

## Setup
Install the latest version into Python 3 library:
```bash
python3 -m pip install -U --user --pre karlsruher
```
*Still in Beta mode: you need to use --pre and expect a moving target.*

### The Robot needs:
+ a *ROBOT_HOME* directory:
    + database file: *ROBOT_HOME/brain*
    + lock file: *ROBOT_HOME/lock*
+ [Twitter API credentials](https://developer.twitter.com)
    + in file *ROBOT_HOME/auth.yaml*
#### Create ROBOT_HOME and auth.yaml:
```bash
export ROBOT_HOME=$HOME/karlsruher
mkdir -p $ROBOT_HOME

cat >$ROBOT_HOME/auth.yaml <<EOF
# You must setup real credentials here:
twitter:
  consumer:
    key: 'YOUR-CONSUMER-KEY'
    secret: 'YOUR-CONSUMER-SECRET'
  access:"
    key: 'YOUR-ACCESS-KEY'
    secret: 'YOUR-ACCESS-SECRET'
EOF
```
#### Populate the database (brain)
The Robot needs to know its *followers*. 
Due to Twitter API rate limits, fetching followers may take up to 1 hour per 1000 followers.
So if you have the time, import followers:
```bash
export ROBOT_HOME=$HOME/karlsruher
karlsruher --home=$ROBOT_HOME -housekeeping [-debug]
```
*Run this once per day, nightly!*

Once the Robot has followers imported, it can start to read its mention timeline:
```bash
export ROBOT_HOME=$HOME/karlsruher
karlsruher --home=$ROBOT_HOME -read [-debug]
```
If you're brave enough, go wild and let the Robot read its mention timeline *and* retweeting all appropriate tweets.
```bash
export ROBOT_HOME=$HOME/karlsruher
karlsruher --home=$ROBOT_HOME -talk [-debug]
```
*Run this every 5 minutes or whatever interval you like.*
