'''
@Karlsruher Retweet Robot
https://github.com/schlind/Karlsruher
'''

import logging
import os
import sys
import sqlite3


from .common import StopWatch
from .common import Lock
from .twitter import Twitter

##
##
class Karlsruher:

    logger = None
    lock = None
    twitter = None

    def __init__(self, config, brain=None, twitter=None):

        home = config.home

        if not os.path.isdir(home):
            raise Exception('Specified home "{}" not a directory. Please specify a valid "home" directory.'.format(home))

        self.do_reply = config.do_reply
        self.do_retweet = config.do_retweet

        self.logger = logging.getLogger(self.__class__.__name__)

        credentials = home + '/credentials.py'
        self.twitter = twitter if twitter else Twitter(credentials)
        self.screen_name = self.twitter.me().screen_name
        self.logger.info('Hello, my name is @%s.', self.screen_name)

        database = home + '/'+ self.screen_name.lower() + '.db'
        self.brain = brain if brain else Brain(database)
        self.logger.info('Having %s.', self.brain.metrics())

        self.advisors = []
        for user in self.twitter.list_advisors():
            self.advisors.append(str(user.id))
        self.logger.info('Having %s advisors.', len(self.advisors))

        self.lock = Lock(home + '/.lock.' + self.screen_name.lower())




    def house_keeping(self):

        if not self.lock.acquire():
            self.logger.debug('Housekeeping locked by "%s".', self.lock.path)
            return False

        self.logger.info('Housekeeping! This may take a while...')

        watch = StopWatch()
        try:
            self.brain.import_users('followers', self.twitter.followers)
            self.brain.import_users('friends', self.twitter.friends)
        except: # pragma: no cover
            self.logger.exception('Exception during housekeeping!')

        self.logger.info('Housekeeping done, took %s.', watch.elapsed())
        self.lock.release()
        return True


    def read_mentions(self):

        if not self.lock.acquire():
            self.logger.debug('Reading locked by "%s".', self.lock.path)
            return False

        self.logger.info('Reading mentions...')

        watch = StopWatch()
        for mention in self.twitter.mentions_timeline():
            try:
                self.read_mention(mention)
            except: # pragma: no cover
                self.logger.exception('Exception while reading mention.')

        self.logger.info('Reading done, took %s.', watch.elapsed())
        self.lock.release()
        return True


    def read_mention(self, tweet):

        tweet_log = '@{}/{}'.format(tweet.user.screen_name, tweet.id)

        if self.brain.has_tweet(tweet):
            self.logger.info('%s read before.', tweet_log)
            return False

        applied_action = 'read_mention'

        for action in [self.advice_action, self.retweet_action]:
            if action(tweet):
                applied_action = action.__name__
                break

        self.brain.add_tweet(tweet, applied_action)
        self.logger.info('%s applied %s.', tweet_log, applied_action)
        return True


    def advice_action(self, tweet):

        if str(tweet.user.id) not in self.advisors:
            self.logger.debug('@%s is not an advisor.', tweet.user.screen_name)
            return False ## not an advisor

        message = str(tweet.text)
        trigger = '@{}!'.format(self.screen_name.lower())
        if not message.lower().startswith(trigger):
            self.logger.debug('@%s gave no advice.', tweet.user.screen_name)
            return False ## not an advice

        advice = message[len(trigger):].strip()

        if advice.lower().startswith('geh schlafen!'):
            self.logger.info(
                'Taking advice from @%s: %s', tweet.user.screen_name, advice
            )
            self.brain.set_value('retweet.disabled', True)
            self.send_reply(tweet, 'Ok @{}, ich retweete nicht mehr... (Automatische Antwort)')
            return True ## took advice

        if advice.lower().startswith('wach auf!'):
            self.logger.info(
                'Taking advice from @%s: %s', tweet.user.screen_name, advice
            )
            self.brain.set_value('retweet.disabled', None)
            self.send_reply(tweet, 'Ok @{}, ich retweete wieder... (Automatische Antwort)')
            return True ## took advice

        return False ## did not take advice


    def send_reply(self, tweet, status):

        status = status.format(tweet.user.screen_name)
        self.logger.debug(
            '%s: "%s"', 'Reply' if self.do_reply else 'Would reply', status
        )
        if self.do_reply:
            self.twitter.update_status(
                in_reply_to_status_id=tweet.id,
                status=status.format(tweet.user.screen_name)
            )


    def retweet_action(self, tweet):

        if self.brain.get_value('retweet.disabled'):
            self.logger.debug('I am sleeping and not retweeting.')
            return False ## no retweets

        if str(tweet.user.screen_name) == str(self.screen_name):
            self.logger.debug('@%s is me, no retweet.', tweet.user.screen_name)
            return False ## not retweeting myself

        if str(tweet.user.protected) == 'True':
            self.logger.debug('@%s protected, no retweet.', tweet.user.screen_name)
            return False ## can't retweet protected users

        if str(tweet.in_reply_to_status_id) != 'None':
            self.logger.debug('@%s reply, no retweet.', tweet.user.screen_name)
            return False ## not retweeting replies

        if not self.brain.has_user('followers', tweet.user.id):
            self.logger.debug('@%s not following, no retweet.', tweet.user.screen_name)
            return False ## not retweeting non-followers

        self.logger.debug(
            '%s: @%s/%s.',
            'Retweet' if self.do_retweet else 'Would retweet',
            tweet.user.screen_name, tweet.id
        )

        if self.do_retweet:
            self.twitter.retweet(tweet)

        return True ## logically retweeted




##
##
class Brain:

    schema = [
        '''CREATE TABLE IF NOT EXISTS config (
            name VARCHAR PRIMARY KEY,
            value VARCHAR DEFAULT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS tweets (
            id VARCHAR PRIMARY KEY,
            user_screen_name VARCHAR NOT NULL,
            reason VARCHAR NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS followers (
            id VARCHAR PRIMARY KEY,
            screen_name VARCHAR NOT NULL,
            state INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''',
        '''CREATE TABLE IF NOT EXISTS friends (
            id VARCHAR PRIMARY KEY,
            screen_name VARCHAR NOT NULL,
            state INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )''',
    ]

    def __init__(self, database):

        self.logger = logging.getLogger(self.__class__.__name__)

        self.connection = sqlite3.connect(database)
        self.connection.row_factory = sqlite3.Row

        for create_table in self.schema:
            self.connection.cursor().execute(create_table)
            self.connection.commit()


    def set_value(self, name, value=None):

        cursor = self.connection.cursor()
        if value is None:
            self.logger.debug('Unsetting value "%s"', name)
            cursor.execute('DELETE FROM config WHERE name = ?', (str(name),))
        else:
            self.logger.debug('Setting value "%s"', name)
            cursor.execute(
                'INSERT OR REPLACE INTO config (name,value) VALUES (?,?)',
                (str(name), str(value))
            )
        self.connection.commit()
        return cursor.rowcount


    def get_value(self, name, default=None):

        self.logger.debug('Getting value "%s"', name)

        cursor = self.connection.cursor()
        cursor.execute('SELECT value FROM config WHERE name = ?', (str(name),))
        value = cursor.fetchone()

        if value:

            read_value = value['value']
            if read_value == 'True':
                return True
            if read_value == 'False':
                return False

            return read_value

        return default


    def has_tweet(self, tweet):

        cursor = self.connection.cursor()
        cursor.execute('SELECT id FROM tweets WHERE id = ?', (str(tweet.id),))
        have = cursor.fetchone() is not None
        self.logger.debug('%s tweet "%s".', 'Having' if have else 'Not having', tweet.id)
        return have


    def add_tweet(self, tweet, reason):

        self.logger.debug('Adding tweet "%s".', tweet.id)

        cursor = self.connection.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO tweets (id,user_screen_name,reason) VALUES (?,?,?)',
            (str(tweet.id), str(tweet.user.screen_name), str(reason))
        )
        self.connection.commit()
        return cursor.rowcount


    def count_tweets(self, user_screen_name=None, reason=None):

        count = 'SELECT COUNT(id) AS count FROM tweets'
        where = ()
        if user_screen_name and reason:
            count += ' WHERE user_screen_name = ? AND reason = ?'
            where = (str(user_screen_name), str(reason))
        elif user_screen_name:
            count += ' WHERE user_screen_name = ?'
            where = (str(user_screen_name),)
        elif reason:
            count += ' WHERE reason = ?'
            where = (str(reason),)

        cursor = self.connection.cursor()
        cursor.execute(count, where)
        count = cursor.fetchone()['count']

        self.logger.debug('Count tweets%s%s: %s.', ' by @' + user_screen_name if user_screen_name else '', ', reason=' + reason if reason else '', count)

        return count


    def users(self, table):

        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT id FROM {} WHERE state > 0'.format(table)
        )
        users = cursor.fetchall()
        self.logger.debug('Fetched %s users from table "%s".', len(users), table)
        return users


    def has_user(self, table, user_id):

        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT id, screen_name FROM {} WHERE state > 0 AND id = ?'.format(table),
            (str(user_id),)
        )
        has_user = cursor.fetchone() is not None
        self.logger.debug(
            '%s user "%s" in "%s".',
            'Having' if has_user else 'Not having', user_id, table
        )
        return has_user


    def import_users(self, table, source):

        limbo = self.connection.cursor()
        limbo.execute('UPDATE {} SET state = 2 WHERE state = 1'.format(table))
        self.connection.commit()

        if callable(source):
            for user in source():
                self.add_user(table, user, 3)
        else:
            for user in source:
                self.add_user(table, user, 3)

        nirvana = self.connection.cursor()
        nirvana.execute('UPDATE {} SET state = 0 WHERE state = 2'.format(table))
        self.connection.commit()

        imported = self.connection.cursor()
        imported.execute('UPDATE {} SET state = 1 WHERE state = 3'.format(table))
        self.connection.commit()

        self.logger.info(
            'Updated %s %s, %s imported, %s lost.',
            limbo.rowcount, table, imported.rowcount, nirvana.rowcount
        )


    def add_user(self, table, user, state=1):

        self.logger.debug(
            'Adding user "%s" to "%s"', user.screen_name, table
        )
        cursor = self.connection.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO {} (id,screen_name,state) VALUES (?,?,?)'.format(table),
            (str(user.id), str(user.screen_name), state)
        )
        self.connection.commit()
        return cursor.rowcount


    def metrics(self):

        cursor = self.connection.cursor()

        cursor.execute('SELECT COUNT(id) AS count FROM tweets')
        tweet_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(id) AS count FROM followers WHERE state > 0')
        follower_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(id) AS count FROM followers WHERE state = 0')
        orphan_follower_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(id) AS count FROM friends WHERE state > 0')
        friend_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(id) AS count FROM friends WHERE state = 0')
        orphan_friend_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(name) AS count FROM config')
        config_count = cursor.fetchone()['count']

        return '{} tweets, {}({}) followers, {}({}) friends, {} config values'.format(
            tweet_count, follower_count, orphan_follower_count,
            friend_count, orphan_friend_count, config_count
        )



##
##
class CommandLine:

    """@Karlsruher Retweet Robot command line

    $ --home=/path/to [-read|-talk|-housekeeping]

  Run Modes:
    -read	Read timelines and trigger activities.
            and add activities:
                -retweet	Send retweets.
                -reply		Send replies.
  or:
    -talk	Combines "-read" and all activities.

  # Cronjob (every 5 minutes):
  */5 * * * * /PATH/karlsruher/cron.sh --home=PATH -talk >/dev/null 2>&1


  or:

    -housekeeping	Perform housekeeping tasks and exit.
        This fetches followers and friends from Twitter.
        Due to API Rate Limits, housekeeping is throttled
        and takes up to 1 hour per 1000 followers/friends.
        Run this nightly once per day.

  # Cronjob (once per day):
  3 3 * * * /PATH/karlsruher/cron.sh --home=PATH -housekeeping >/dev/null 2>&1


  or:

    -help	You are reading this right now.


  Add "-debug" to raise overall logging level.
    """

    @staticmethod
    def home():

        home = None
        __home = '--home='
        for arg in sys.argv:
            if arg.startswith(__home):
                home = arg[len(__home):]

        if not home:
            raise Exception('No home directory specified! Specify with "--home=/path/to/home".')

        if not os.path.isdir(home):
            raise Exception('Specified home "{}" not a directory, aborting.'.format(home))

        return home


    @staticmethod
    def run():

        logging.basicConfig(
            level=logging.DEBUG if '-debug' in sys.argv else logging.INFO,
            format='%(asctime)s %(levelname)-5.5s [%(name)s.%(funcName)s]: %(message)s',
            handlers=[logging.StreamHandler()]
        )

        run_commands = ['-housekeeping', '-read', '-talk']
        is_command = False
        for command in run_commands:
            if command in sys.argv:
                is_command = True

        if is_command:
            try:

                config = Config.create(
                    home=CommandLine.home(),
                    do_reply='-reply' in sys.argv or '-talk' in sys.argv,
                    do_retweet='-retweet' in sys.argv or '-talk' in sys.argv
                )

                instance = Karlsruher(config)

                if '-housekeeping' in sys.argv:
                    return 0 if instance.house_keeping() else 1
                if '-read' in sys.argv or '-talk' in sys.argv:
                    return 0 if instance.read_mentions() else 1

            except Exception as message:
                print(message)
                return 1

        print(CommandLine.__doc__)
        return 0



##
##
class Config:

    @staticmethod
    def create(home, do_reply=False, do_retweet=False):
        config = Config()
        config.home = home
        config.do_reply = do_reply
        config.do_retweet = do_retweet
        return config
