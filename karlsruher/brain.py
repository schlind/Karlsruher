'''
Using SQLite3 Database as Brain
'''

import logging
import sqlite3

class Brain:
    '''
    Provide persistent memories in a simple SQLite3 database table.
    '''

    def __init__(self, database=':memory:'):
        '''
        :param database: The sqlite3 database connection string,
                            using in-memory database as default.
        '''
        self.logger = logging.getLogger(__class__.__name__)
        self.connection = sqlite3.connect(database=database)
        self.connection.row_factory = sqlite3.Row
        self.connection.cursor().execute('''
            CREATE TABLE IF NOT EXISTS brain (
                space VARCHAR NOT NULL,
                entry VARCHAR NOT NULL,
                data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (space, entry)
            )''')
        self.connection.commit()

    def __repr__(self):
        ''':return: Database metrics as string representation.'''
        cursor = self.connection.cursor()
        cursor.execute("SELECT space, COUNT(entry) AS count FROM brain GROUP BY space")
        string = 'Having'
        for item in cursor.fetchall():
            string += ' {1} {0}s,'.format(item['space'], str(item['count']))
        if string[len(string) - 1] == ',':
            string = string[:len(string) - 1]
        return string + '.'


    # Read:

    def has(self, space, entry):
        '''
        Indicate whether brain has the given entry or not.

        :param space: The space.
        :param entry: The entry.
        :return: True if brain has the given entry, otherwise False.
        '''
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT entry FROM brain WHERE space=? AND entry=?', (str(space), str(entry),)
        )
        have = cursor.fetchone() is not None
        self.logger.debug('%s %s %s', 'Having' if have else 'Not having', space, entry)
        return have


    def get(self, space, entry):
        '''
        Provide the data of the specified entry, implement a READ operation.

        :param space: The space.
        :param entry: The entry.
        :return: The data of the entry, maybe None.
        '''
        cursor = self.connection.cursor()
        cursor.execute(
            'SELECT data FROM brain WHERE space=? AND entry=?', (str(space), str(entry),)
        )
        data = cursor.fetchone()
        self.logger.debug('%s %s %s', 'Having' if data else 'Not having', space, entry)
        return data['data'] if data else None


    # Create & update:

    def store(self, space, entry, data=None):
        '''
        Store the specified entry, implement a CREATE and UPDATE operation.

        :param space: The space.
        :param entry: The entry.
        :param data: The data, optional.
        :return: Number of affected rows in database, either 0 or 1.
        '''
        self.logger.debug('Store %s %s %s', space, entry, data)
        cursor = self.connection.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO brain (space, entry, data) VALUES (?,?,?)',
            (str(space), str(entry), data,)
        )
        self.connection.commit()
        return cursor.rowcount


    def forget(self, space, entry=None):
        '''
        Forget entries, implement a DELETE operation.

        :param space: The space.
        :param entry: The entry.
        :return: Number of affected rows in database.
        '''
        self.logger.debug('Forget %s %s', space, entry if entry else 'any')
        cursor = self.connection.cursor()
        if entry:
            cursor.execute('DELETE FROM brain WHERE space=? AND entry=?', (str(space), str(entry),))
        else:
            cursor.execute('DELETE FROM brain WHERE space=?', (str(space),))
        self.connection.commit()
        return cursor.rowcount
