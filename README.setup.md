# Karlsruher Twitter Robot
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
* [Twitter API credentials](https://developer.twitter.com) in file *$HOME/karlsruher/auth.yaml*:
```
twitter:
  consumer:
    key: 'YOUR-CONSUMER-KEY'
    secret: 'YOUR-CONSUMER-SECRET'
  access:
    key: 'YOUR-ACCESS-KEY'
    secret: 'YOUR-ACCESS-SECRET'
```

```
echo "" >$HOME/karlsruher/auth.yaml
echo "twitter:" >>$HOME/karlsruher/auth.yaml
echo "  consumer:" >>$HOME/karlsruher/auth.yaml
echo "    key: 'YOUR-CONSUMER-KEY'" >>$HOME/karlsruher/auth.yaml
echo "    secret: 'YOUR-CONSUMER-SECRET'" >>$HOME/karlsruher/auth.yaml
echo "  access:" >>$HOME/karlsruher/auth.yaml
echo "    key: 'YOUR-ACCESS-KEY'" >>$HOME/karlsruher/auth.yaml
echo "    secret: 'YOUR-ACCESS-SECRET'" >>$HOME/karlsruher/auth.yaml
```
## Run
```
karlsruher --home=$HOME/karlsruher -help
```
