# -*- coding: utf-8 -*-
import os
import mysql.connector
from mysql.connector import errorcode
from tables import TABLES

from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


class DbConnector:
    def __init__(self, user, password, host, database=None):
        self.user = user
        self.password = password
        self.host = host
        self.database = database

    def _create_connection(self):
        try:
            cnx = mysql.connector.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                database=self.database,
                use_unicode=True,
                charset='utf8mb4'
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        return cnx

    def create_database(self, db_name):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        try:
            cursor.execute(
                "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
        except mysql.connector.Error as err:
            print("Failed creating database: {}".format(err))
            exit(1)
        self.database = db_name

    def create_tables(self, *tables):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        for table in tables:
            try:
                cursor.execute(table)
            except mysql.connector.Error as err:
                print("Failed creating table: {}".format(err))
                cursor.close()
                cnx.close()
                exit(1)
        cursor.close()
        cnx.close()

    def add_user(self, user_id, date):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        add_user = (
            'INSERT INTO users (id, first_addressing) '
            'VALUES '
            '(%s, %s);'
        )
        cursor.execute(add_user, (user_id, date))
        cnx.commit()
        cursor.close()
        cnx.close()

    def tag(self, tags_names):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        result = []
        for name in tags_names:
            tags_query = (
                'SELECT CONCAT("%23", name, " - ", definition) FROM tags '
                'WHERE name=%s'
            )
            cursor.execute(tags_query, (name,))
            try:
                result.append(next(cursor)[0])
            except StopIteration:
                break
        cursor.close()
        cnx.close()
        return '%0A'.join(result)

    def _get_tag_id(self, *tags_names):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        result = []
        for name in tags_names:
            tags_query = (
                'SELECT id FROM tags '
                'WHERE name=%s'
            )
            cursor.execute(tags_query, (name,))
            try:
                result.append(next(cursor)[0])
            except StopIteration:
                break
        cursor.close()
        cnx.close()
        return result

    def write(self, date, text, user_id, tags_names):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        add_message = (
            'INSERT INTO messages (date, text, user_id) '
            'VALUES '
            '    (%s, %s, %s);'
        )
        cursor.execute(add_message, (date, text, user_id))
        message_id = cursor.lastrowid
        add_last_message = (
            'UPDATE users '
            'SET last_message_id=%s '
            'WHERE id=%s;'
        )
        cursor.execute(add_last_message, (message_id, user_id))
        tags = self._get_tag_id(*tags_names)
        for tag_id in tags:
            self._add_message_tag(cursor, message_id, tag_id)
        cnx.commit()
        cursor.close()
        cnx.close()
        return u'заметка {0} сохранена'.format(message_id)

    def _add_message_tag(self, cursor, message_id, tag_id):
        add_message_tag = (
            'INSERT INTO messages_tags (message_id, tag_id) '
            'VALUES '
            '    (%s, %s);'
        )
        cursor.execute(add_message_tag, (message_id, tag_id))

    def write_tag(self, tag_name, tag_definition):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        find_tag = (
            'SELECT id FROM tags '
            'WHERE name=%s;'
        )
        cursor.execute(find_tag, (tag_name,))
        try:
            tag_id = next(cursor)[0]
            update_tag = (
                'UPDATE tags '
                'SET definition=%s '
                'WHERE id=%s;'
            )
            cursor.execute(update_tag, (tag_definition, tag_id))
        except StopIteration:
            add_tag = (
                'INSERT INTO tags (name, definition) '
                'VALUES '
                '    (%s, %s);'
            )
            cursor.execute(add_tag, (tag_name, tag_definition))
        finally:
            cnx.commit()
            cursor.close()
            cnx.close()    

    def read_last(self, user_id):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        text_query = (
            'SELECT text FROM messages '
            'JOIN users ON users.last_message_id=messages.id '
            'WHERE users.id=%s;'
        )
        cursor.execute(text_query, (user_id,))
        try:
            text, = next(cursor)
        except StopIteration:
            return u''
        cursor.close()
        cnx.close()
        return text.replace('#', '%23')

    def read(self, user_id, message_id):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        text_query = (
            'SELECT text, user_id FROM messages '
            'WHERE id=%s;'
        )
        cursor.execute(text_query, (message_id,))
        try:
            text, owner_id = next(cursor)
        except StopIteration:
            cursor.close()
            cnx.close()
            return u'заметка {0} не найдена'.format(message_id)
        cursor.close()
        cnx.close()
        if user_id == owner_id:
            return text.replace('#', '%23')
        return (u'заметка {0} принадлежит другому '
                u'пользователю').format(message_id)

    def read_all(self, user_id):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        text_query = (
            'SELECT text FROM messages '
            'WHERE user_id=%s;'
        )
        cursor.execute(text_query, (user_id,))
        result = [row[0].replace('#', '%23') for row in cursor]
        cursor.close()
        cnx.close()
        return '%0A%0A'.join(result)

    def read_tag(self, user_id, tag_name):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        text_query = (
            'SELECT text FROM messages '
            'JOIN messages_tags ON messages.id = messages_tags.message_id '
            'JOIN tags ON tags.id = messages_tags.tag_id '
            'WHERE user_id=%s AND tags.name=%s;'
        )
        cursor.execute(text_query, (user_id, tag_name))
        result = [row[0].replace('#', '%23') for row in cursor]
        cursor.close()
        cnx.close()
        return '%0A%0A'.join(result)

    def tag_all(self):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        text_query = 'SELECT CONCAT("%23", name, "-", definition) FROM tags;'
        cursor.execute(text_query)
        result = [row[0] for row in cursor]
        cursor.close()
        cnx.close()
        return '%0A%0A'.join(result)
