# Karlsruher Twitter Robot
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
            """CREATE TABLE IF NOT EXISTS names_values (
                name VARCHAR PRIMARY KEY,
                value VARCHAR DEFAULT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS users (
                user_type VARCHAR NOT NULL,
                user_id VARCHAR NOT NULL,
                screen_name VARCHAR NOT NULL,
                state INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_type, user_id)
            )""",
            """CREATE TABLE IF NOT EXISTS tweets (
                tweet_type VARCHAR NOT NULL,
                tweet_id VARCHAR NOT NULL,
                user_screen_name VARCHAR NOT NULL,
                user_id VARCHAR NOT NULL,
                comment VARCHAR NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (tweet_type, tweet_id)
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
            cursor.execute(
                'DELETE FROM names_values WHERE name = ?',
                (str(name),)
            )
        else:
            self.logger.debug('Setting value "%s"', name)
            cursor.execute(
                'INSERT OR REPLACE INTO names_values (name,value) VALUES (?,?)',
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
        cursor.execute('SELECT value FROM names_values WHERE name = ?', (str(name),))
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

    def has_user(self, user_type, user_id):
        """
        Indicate whether a user exists in the specified table or not.

        :param user_type:
        :param user_id:
        :return:
        """
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT user_id FROM users WHERE state > 0 AND user_type = ? AND user_id = ?',
            (str(user_type), str(user_id),)
        )
        having = cursor.fetchone() is not None
        self.logger.debug('%s %s %s.', 'Having' if having else 'Not having', user_type, user_id)
        return having

    def users(self, user_type):
        """
        Provide all users from the specified table.

        :param user_type:
        :return: List of users with state>0 in the specified table
        """
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT user_id FROM users WHERE state > 0 and user_type = ?',
            (str(user_type),)
        )
        users = cursor.fetchall()
        self.logger.debug('Fetched %s users from table "%s".', len(users), user_type)
        return users

    def import_users(self, user_type, callable_source):
        """
        Import users from the given source into the specified table.

        :param user_type:
        :param callable_source:
        :return:
        """
        # 1. All active/state=1 users go limbo/state=2
        limbo = self.connection.cursor()
        limbo.execute(
            'UPDATE users SET state = 2 WHERE state = 1 AND user_type = ?',
            (str(user_type),)
        )
        self.connection.commit()
        # 2. Import users go imported/state=3
        for user in callable_source():
            self.add_user(user_type, user, 3)
        # 3. All limbo/state=2 users go deleted/state=0
        nirvana = self.connection.cursor()
        nirvana.execute(
            'UPDATE users SET state = 0 WHERE state = 2 AND user_type = ?',
            (str(user_type),)
        )
        self.connection.commit()
        # 4. All imported/state=3 users go active/state=1
        imported = self.connection.cursor()
        imported.execute(
            'UPDATE users SET state = 1 WHERE state = 3 AND user_type = ?',
            (str(user_type),)
        )
        self.connection.commit()
        self.logger.info(
            'Updated %s %ss, %s imported, %s lost.',
            limbo.rowcount, user_type, imported.rowcount, nirvana.rowcount
        )

    def add_user(self, user_type, user, state=1):
        """
        Store a user in the specified table.

        :param user_type:
        :param user:
        :param state:
        :return:
        """
        self.logger.debug('Adding @%s to "%s" table.', user.screen_name, user_type)
        cursor = self.connection.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO users ({0}) VALUES ({1})'.format(
                'user_type,user_id,screen_name,state',
                '?,?,?,?'
            ),
            (str((user_type)), str(user.id), str(user.screen_name), state)
        )
        self.connection.commit()
        return cursor.rowcount

    # Aliases:

    def has_follower(self, user_id):
        """
        :param user_id:
        :return:
        """
        return self.has_user('follower', user_id)

    def has_friend(self, user_id):
        """
        :param user_id:
        :return:
        """
        return self.has_user('friend', user_id)

    def import_followers(self, callable_source):
        """
        :param callable_source:
        """
        self.import_users('follower', callable_source)

    def import_friends(self, callable_source):
        """
        :param callable_source:
        """
        self.import_users('friend', callable_source)

    # Remember tweets:

    def has_tweet(self, tweet_type, tweet_id):
        """
        Indicate whether a tweet is stored or not.

        :param tweet: The tweet
        :return: True if the tweet is stored, otherwise False
        """
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT tweet_id FROM tweets WHERE tweet_type = ? AND tweet_id = ?',
            (str(tweet_type), str(tweet_id),)
        )
        have_tweet = cursor.fetchone() is not None
        self.logger.debug('%s tweet "%s".', 'Having' if have_tweet else 'Not having', tweet_id)
        return have_tweet

    def add_tweet(self, tweet_type, tweet, comment=None):
        """
        Store a tweet for a specified reason.

        :param tweet_type: The type of the tweet
        :param tweet: The tweet
        :param reason: The reason
        :return: The rowcount of the underlying database operation
        """
        self.logger.debug('Adding tweet "%s".', tweet.id)
        cursor = self.connection.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO tweets ({0}) VALUES ({1})'.format(
                'tweet_type,tweet_id,user_screen_name,user_id,comment',
                '?,?,?,?,?'
            ),
            (str(tweet_type), str(tweet.id), str(tweet.user.screen_name),
             str(tweet.user.id), str(comment))
        )
        self.connection.commit()
        return cursor.rowcount

    def count_tweets(self, tweet_type=None, comment=None):
        """
        Count tweets.

        :param tweet_type:
        :param comment:
        :return: The count of tweets
        """
        where = ''
        param = ()
        if tweet_type and comment:
            where = 'WHERE tweet_type = ? AND comment = ?'
            param = (str(tweet_type), str(comment),)
        elif tweet_type:
            where = 'WHERE tweet_type = ?'
            param = (str(tweet_type),)
        elif comment:
            where = 'WHERE comment = ?'
            param = (str(comment),)

        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT COUNT(tweet_id) AS count FROM tweets {}'.format(where),
            param
        )
        count = cursor.fetchone()['count']
        self.logger.debug('Counting %s tweets %s %s.', count, tweet_type, comment)
        return count

    # Provide metrics:

    def metrics(self):
        """
        Provide simple database metrics.

        :return: Metrics as string.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(name) AS count FROM names_values")
        named_values_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(tweet_id) AS count FROM tweets")
        tweet_count = cursor.fetchone()['count']
        select_users = "SELECT COUNT(user_id) AS count FROM users WHERE {}"
        cursor.execute(select_users.format("user_type = 'follower' AND state > 0"))
        follower_count = cursor.fetchone()['count']
        cursor.execute(select_users.format("user_type = 'friend' AND state > 0"))
        friend_count = cursor.fetchone()['count']
        return '{} tweets, {} followers, {} friends, {} named values'.format(
            tweet_count, follower_count, friend_count, named_values_count
        )
