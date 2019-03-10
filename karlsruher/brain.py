# Karlsruher Retweet Robot
# https://github.com/schlind/Karlsruher
"""
The brain of a robot
"""

import logging
import sqlite3


class Brain:
    """
    Provide persistent memories.
    """

    # Static:

    @staticmethod
    def __schema():
        """
        :return: The database schema
        """
        return [

            # Table for unspecified key/value data:
            """CREATE TABLE IF NOT EXISTS config (
                name VARCHAR PRIMARY KEY,
                value VARCHAR DEFAULT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",

            # Table for tweet meta information:
            """CREATE TABLE IF NOT EXISTS tweets (
                id VARCHAR PRIMARY KEY,
                user_screen_name VARCHAR NOT NULL,
                reason VARCHAR NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",

            # Table for followers:
            """CREATE TABLE IF NOT EXISTS followers (
                id VARCHAR PRIMARY KEY,
                screen_name VARCHAR NOT NULL,
                state INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",

            # Table for friends:
            """CREATE TABLE IF NOT EXISTS friends (
                id VARCHAR PRIMARY KEY,
                screen_name VARCHAR NOT NULL,
                state INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )"""
        ]

    # Instance:

    def __init__(self, database):
        """
        :param database: The sqlite3 database connection string
        """
        self.logger = logging.getLogger(__class__.__name__)
        self.connection = sqlite3.connect(database=database)
        self.connection.row_factory = sqlite3.Row
        for create_table in Brain.__schema():
            self.connection.cursor().execute(create_table)
            self.connection.commit()

    # Set and get values:

    def set(self, name, value=None):
        """
        Store a named value.

        :param name: The name of the value
        :param value: The value, give None to unset the value
        :return: The rowcount of the underlying database operation
        """
        cursor = self.connection.cursor()
        if value is None:
            self.logger.debug('Removing value "%s"', name)
            cursor.execute('DELETE FROM config WHERE name = ?', (str(name),))
        else:
            self.logger.debug('Setting value "%s"', name)
            cursor.execute(
                'INSERT OR REPLACE INTO config (name,value) VALUES (?,?)',
                (str(name), str(value))
            )
        self.connection.commit()
        return cursor.rowcount

    def get(self, name, default=None):
        """
        Provide a stored named value or the default if no value exists.

        :param name: The name of the value to provide
        :param default: The default to return if value is not set
        :return: The value if present, otherwise the provided default.
            String values "True" and "False" are returned as their boolean representation.
        """
        self.logger.debug('Getting value for "%s"', name)
        cursor = self.connection.cursor()
        cursor.execute('SELECT value FROM config WHERE name = ?', (str(name),))
        value = cursor.fetchone()
        if not value:
            return default
        the_value = value['value']
        if the_value == 'True':
            return True
        if the_value == 'False':
            return False
        return the_value

    # Know users:

    def has_user(self, table, user_id):
        """
        Indicate whether a user exists in the specified table or not.

        :param table:
        :param user_id:
        :return:
        """
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

    def users(self, table):
        """
        Provide all users from the specified table.

        :param table:
        :return: List of users with state>0 in the specified table
        """
        cursor = self.connection.cursor()
        cursor.execute('SELECT id FROM {} WHERE state > 0'.format(table))
        users = cursor.fetchall()
        self.logger.debug('Fetched %s users from table "%s".', len(users), table)
        return users

    def import_users(self, table, callable_source):
        """
        Import users from the given source into the specified table.

        :param table:
        :param callable_source:
        :return:
        """
        # 1. All active/state=1 users go limbo/state=2
        limbo = self.connection.cursor()
        limbo.execute('UPDATE {} SET state = 2 WHERE state = 1'.format(table))
        self.connection.commit()
        # 2. Import users go imported/state=3
        for user in callable_source():
            self.add_user(table, user, 3)
        # 3. All limbo/state=2 users go deleted/state=0
        nirvana = self.connection.cursor()
        nirvana.execute('UPDATE {} SET state = 0 WHERE state = 2'.format(table))
        self.connection.commit()
        # 4. All imported/state=3 users go active/state=1
        imported = self.connection.cursor()
        imported.execute('UPDATE {} SET state = 1 WHERE state = 3'.format(table))
        self.connection.commit()
        self.logger.info(
            'Updated %s %s, %s imported, %s lost.',
            limbo.rowcount, table, imported.rowcount, nirvana.rowcount
        )

    def add_user(self, table, user, state=1):
        """
        Store a user in the specified table.

        :param table:
        :param user:
        :param state:
        :return:
        """
        self.logger.debug('Adding @%s to "%s" table.', user.screen_name, table)
        cursor = self.connection.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO {} (id,screen_name,state) VALUES (?,?,?)'.format(table),
            (str(user.id), str(user.screen_name), state)
        )
        self.connection.commit()
        return cursor.rowcount

    # Aliases:

    def has_follower(self, user_id):
        """
        :param user_id:
        :return:
        """
        return self.has_user('followers', user_id)

    def has_friend(self, user_id):
        """
        :param user_id:
        :return:
        """
        return self.has_user('friends', user_id)

    def import_followers(self, callable_source):
        """
        :param callable_source:
        """
        self.import_users('followers', callable_source)

    def import_friends(self, callable_source):
        """
        :param callable_source:
        """
        self.import_users('friends', callable_source)

    # Remember tweets:

    def has_tweet(self, tweet):
        """
        Indicate whether a tweet is stored or not.

        :param tweet: The tweet
        :return: True if the tweet is stored, otherwise False
        """
        cursor = self.connection.cursor()
        cursor.execute('SELECT id FROM tweets WHERE id = ?', (str(tweet.id),))
        have_tweet = cursor.fetchone() is not None
        self.logger.debug('%s tweet "%s".', 'Having' if have_tweet else 'Not having', tweet.id)
        return have_tweet

    def add_tweet(self, tweet, reason='add_tweet'):
        """
        Store a tweet for a specified reason.

        :param tweet: The tweet
        :param reason: The reason
        :return: The rowcount of the underlying database operation
        """
        self.logger.debug('Adding tweet "%s".', tweet.id)
        cursor = self.connection.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO tweets (id,user_screen_name,reason) VALUES (?,?,?)',
            (str(tweet.id), str(tweet.user.screen_name), str(reason))
        )
        self.connection.commit()
        return cursor.rowcount

    def count_tweets(self, user_screen_name=None, reason=None):
        """
        Count tweets.

        :param user_screen_name:
        :param reason:
        :return: The count of tweets
        """
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
        self.logger.debug('Count tweets%s%s: %s.',
                          ' by @' + user_screen_name if user_screen_name else '',
                          ', reason=' + reason if reason else '', count)
        return count

    # Provide metrics:

    def metrics(self):
        """
        Provide simple database metrics.

        :return: Metrics as string.
        """
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
