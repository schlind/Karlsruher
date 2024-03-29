# @Karlsruher
* is a robot on Twitter ([Link](https://twitter.com/Karlsruher))
* retweets mentions from its followers when they apply some rules
---

## Setup instructions

#### Prerequisites:
* Python 3 environment (tested with 3.5 on Linux, 3.8.5 MacOS)
* The Robot needs a home directory for its work
* You need [Twitter API credentials](https://developer.twitter.com) for your Robot

#### Install the latest release into your Python 3 library:
```bash
$ python3 -m pip install -U --user --pre karlsruher
```
*Still in Beta mode: --pre and expect a moving target!*

#### Create a home directory
You might want to use a different path here:
```bash
export ROBOT_HOME=$HOME/karlsruher
mkdir -p $ROBOT_HOME
```
#### Create auth.yaml credentials file
You want to enter your own credentials here:
```bash
export ROBOT_HOME=$HOME/karlsruher
cat >$ROBOT_HOME/auth.yaml <<EOF
# You must enter real credentials here:
twitter:
  consumer:
    key: 'YOUR-CONSUMER-KEY'
    secret: 'YOUR-CONSUMER-SECRET'
  access:"
    key: 'YOUR-ACCESS-KEY'
    secret: 'YOUR-ACCESS-SECRET'
EOF
```

#### Setup complete

## First run
#### The Robot needs to fetch its followers and friends from Twitter regularly. Run this initially and then once per day:
```bash
export ROBOT_HOME=$HOME/karlsruher
karlsruher --home=$ROBOT_HOME -housekeeping
```

#### To just perfom the desired retweet feature run this at your desired interval:
```bash
export ROBOT_HOME=$HOME/karlsruher
karlsruher --home=$ROBOT_HOME -retweet 
```

### To delete aged tweets run this:
```bash
export ROBOT_HOME=$HOME/karlsruher
karlsruher --home=$ROBOT_HOME -forget 
```


#### Crontab example:
```
*/5 * * * * karlsruher --home=ROBOT_HOME -retweet >>ROBOT_HOME/log 2>&1
1 23 * * * karlsruher --home=ROBOT_HOME -forget >>ROBOT_HOME/log 2>&1
3 3 * * *   karlsruher --home=ROBOT_HOME -housekeeping >>ROBOT_HOME/log 2>&1
```

#### Simple logfile rotation:

```
# cat /etc/logrotate.d/karlsruher
ROBOT_HOME/log {
        rotate 7
        daily
        compress
        missingok
        notifempty
}
```
