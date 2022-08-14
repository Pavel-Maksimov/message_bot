# -*- coding: utf-8 -*-
import os
import mysql.connector
from mysql.connector import errorcode
from tables import TABLES

from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# conn = DbConnector(**db)

db = {
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST')
}

cnx = mysql.connector.connect(**db)
cursor = cnx.cursor()


class DbConnector:
    def __init__(self, user, password, host, database):
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
            '({0}, "{1}");'
        )
        cursor.execute(add_user.format(user_id, date))
        cnx.commit()
        cursor.close()
        cnx.close()

    def tag(self, *tags_names):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        result = []
        for name in tags_names:
            tags_query = (
                'SELECT * FROM tags '
                'WHERE name="{0}"'
            )
            cursor.execute(tags_query.format(name))
            for row in cursor:
                result.append(row)
        cursor.close()
        cnx.close()
        return result

    def add_message(self, date, text, user_id, *tags_names):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        add_message = (
            'INSERT INTO messages (date, text, user_id) '
            'VALUES '
            '    ("{0}", "{1}", {2});'
        )
        cursor.execute(add_message.format(date, text, user_id))
        message_id = cursor.lastrowid
        add_last_message = (
            'UPDATE users '
            'SET last_message_id={0} '
            'WHERE id={1};'
        )
        cursor.execute(add_last_message.format(message_id, user_id))
        tags = self.tag(*tags_names)
        for tag in tags:
            tag_id = tag[0]
            self._add_message_tag(cursor, message_id, tag_id)
        cnx.commit()
        cursor.close()
        cnx.close()
        return message_id

    def _add_message_tag(self, cursor, message_id, tag_id):
        add_message_tag = (
            'INSERT INTO messages_tags (message_id, tag_id) '
            'VALUES '
            '    ("{0}", "{1}");'
        )
        cursor.execute(add_message_tag.format(message_id, tag_id))

    def add_tag(self, name, definition):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        add_tag = (
            'INSERT INTO tags (name, definition) '
            'VALUES '
            '    ("{0}", "{1}");'
        )
        cursor.execute(add_tag.format(name, definition))
        cnx.commit()
        cursor.close()
        cnx.close()    

    def read_last(self, user_id):
        cnx = self._create_connection()
        cursor = cnx.cursor()
        text_query = (
            'SELECT text FROM messages '
            'JOIN users ON users.last_message_id=messages.id '
            'WHERE users.id={0};'
        )
        cursor.execute(text_query.format(user_id))
        result = [row for row in cursor]
        cursor.close()
        cnx.close()
        return result


db['database'] = os.environ.get('DB_NAME')
