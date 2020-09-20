'''
Database
'''

import logging
import sqlite3

class Brain:
    '''Provide persistent memories for a Robot'''

    def __init__(self, database):
        '''
        :param database: The sqlite3 database connection string
        '''
        self.logger = logging.getLogger(__class__.__name__)
        self.connection = sqlite3.connect(database=database)
        self.connection.row_factory = sqlite3.Row
        for create_table in [
            '''CREATE TABLE IF NOT EXISTS tweets (
                tweet_id VARCHAR PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )''',
            '''CREATE TABLE IF NOT EXISTS users (
                user_type VARCHAR NOT NULL,
                user_id VARCHAR NOT NULL,
                state INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_type, user_id)
            )'''
        ]:
            self.connection.cursor().execute(create_table)
            self.connection.commit()

    def __repr__(self):
        '''
        :return: Brain metrics as string.
        '''
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(tweet_id) AS count FROM tweets")
        tweets = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(user_id) AS count FROM users")
        users = cursor.fetchone()['count']
        return 'Brain has {} tweets and {} users.'.format(tweets, users)



    # Remember tweets:

    def find_tweet(self, tweet_id):
        '''
        :param tweet_id: The tweet ID to find
        :return: True if the tweet was found, otherwise False
        '''
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT tweet_id FROM tweets WHERE tweet_id = ?',
            (str(tweet_id),)
        )
        have_tweet = cursor.fetchone() is not None
        self.logger.debug('%s tweet %s.', 'Having' if have_tweet else 'Not having', tweet_id)
        return have_tweet

    def store_tweet(self, tweet_id):
        '''
        :param tweet_id: The tweet ID to add
        :return: Number of affected rows in database, either 0 or 1
        '''
        self.logger.debug('Adding mention "%s".', tweet_id)
        cursor = self.connection.cursor()
        cursor.execute(
            'INSERT OR IGNORE INTO tweets (tweet_id) VALUES (?)',
            (str(tweet_id),)
        )
        self.connection.commit()
        return cursor.rowcount



    # Know users:

    def find_user(self, user_type, user_id):
        '''
        :param user_type: The user type to find
        :param user_id: The user ID to find
        :return: True if the user was found, otherwise False
        '''
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT user_id FROM users WHERE state > 0 AND user_type = ? AND user_id = ?',
            (str(user_type), str(user_id),)
        )
        having = cursor.fetchone() is not None
        self.logger.debug('%s %s %s.', 'Having' if having else 'Not having', user_type, user_id)
        return having

    def store_user(self, user_type, user_id, state=1):
        '''
        :param user_type: The user type to add
        :param user_id: The user ID to add
        :param state: Optional, the state to set, default is 1
        :return: Number of affected rows in database, either 0 or 1
        '''
        self.logger.debug('Adding %s %s to users table.', user_type, user_id)
        cursor = self.connection.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO users ({0}) VALUES ({1})'
                .format('user_type,user_id,state','?,?,?'),
            (str((user_type)), str(user_id), state)
        )
        self.connection.commit()
        return cursor.rowcount

    def import_users(self, user_type, callable_user_id_generator):
        '''
        :param user_type: The user type to add
        :param callable_user_id_generator: The generator that provides user IDs
        '''
        # 1. All active/state=1 users go limbo/state=2:
        limbo = self.connection.cursor()
        limbo.execute(
            'UPDATE users SET state = 2 WHERE state = 1 AND user_type = ?',
            (str(user_type),)
        )
        self.connection.commit()
        # 2. Import users go imported state=3:
        for user in callable_user_id_generator():
            self.store_user(user_type, user, 3)
        # 3. All limbo/state=2 users go deleted state=0
        nirvana = self.connection.cursor()
        nirvana.execute(
            'UPDATE users SET state = 0 WHERE state = 2 AND user_type = ?',
            (str(user_type),)
        )
        self.connection.commit()
        # 4. All imported/state=3 users go active state=1:
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
