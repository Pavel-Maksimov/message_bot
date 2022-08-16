# -*- coding: utf-8 -*-
import logging
from logging.handlers import RotatingFileHandler
import os

from dotenv import load_dotenv
import mysql.connector
from mysql.connector import errorcode

from tables import TABLES


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    'bot_logs.log',
    maxBytes=1000000,
    backupCount=5
)
formatter = logging.Formatter(
    '%(asctime)s - %(name)-12s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


DB = {
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST')
}


class DbConnector:
    """
    Интерфейс для взаимодействия с базой данных.

    При создании нового класса принимает следующие аргументы:
    -user: имя пользователя базы данных, имеющий доступ к СУБД;
    -password - пароль пользователя;
    -host - имя хоста или ip-адрес сервера СУБД;
    -datebase - имя базы данных (опционально).

    Имеет следующие методы:
    open_connection() - создает соединение с базой данных
    close_connection() - закрывает соединение с базой данных
    create_database(name) - создает новую базу данных
    create_tables(seq) - создает таблицы, переданные в виде 
                         последовательности строк, содержащих 
                         SQL-запросы по созданию таблиц;
    add_user(user_id) - добавляет нового пользователя в базу
    tag(seq) - принимет последовательность строк с именами тэгов
               и возвращает строку с их описанием;
    write(date, text, user_id, tags_names) - 
               добавляет новое сообщение в базу. Принимает дату, 
               текст, id пользователя и имена тегов, связанных с ним.
               Возвращает строку с уведомлением о сохранении сообщения 
               и его id. 
    write_tag(name, definition) - добавляет новый тэг;
    read_last(usеr_id) - принимет id пользователя и возвращает
                         последнее сохраненное сообщение от него;
    read(user_id, message_id) - принимет id пользователя и id сообщения
                                и возвращает последнее сохраненное 
                                сообщение от него;
    read_all(user_id) - принимет id пользователя и возвращает все 
                        его сообщения;
    read_tag(user_id, tag_name) - принимет id пользователя и имя тега
                                  и возвращает все его сообщения, 
                                  связанные с указанным тегом;
    tag_all()  - возвращает все имеющиеся в базе тэги.
    """
    def __init__(self, user, password, host, database=None):
        self.user = user
        self.password = password
        self.host = host
        self.database = database
        self.cnx = None

    def open_connection(self):
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
                logger.error('Неверное имя пользователя или пароль')
                raise
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logger.error('Базы данных {} не существует'.format(self.database))
                raise
            else:
                logger.error(err)
                raise
        self.cnx = cnx

    def close_connection(self):
        self.cnx.close()

    def create_database(self, db_name):
        cursor = self.cnx.cursor()
        try:
            cursor.execute(
                "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_name))
        except mysql.connector.Error as err:
            logger.error(err)
            exit(1)
        self.database = db_name

    def create_tables(self, *tables):
        cursor = self.cnx.cursor()
        try:
            db_name = os.environ.get('DB_NAME')
            cursor.execute("USE {}".format(db_name))
        except mysql.connector.Error as err:
            logger.error('Базы данных {} не существует'.format(db_name))
            raise
        for table in tables:
            try:
                cursor.execute(table)
            except mysql.connector.Error as err:
                logger.error(err)
                cursor.close()
                self.close_connection()
                exit(1)
        cursor.close()

    def add_user(self, user_id, date):
        cursor = self.cnx.cursor()
        check_user_exists = (
            'SELECT count(*) FROM users '
            'WHERE id=%s;'
        )
        cursor.execute(check_user_exists, (user_id,))
        count = int(next(cursor)[0])
        if count != 0:
            cursor.close()
            return
        add_user = (
            'INSERT INTO users (id, first_addressing) '
            'VALUES '
            '    (%s, %s);'
        )
        cursor.execute(add_user, (user_id, date))
        self.cnx.commit()
        cursor.close()

    def tag(self, tags_names):
        cursor = self.cnx.cursor()
        result = []
        for name in tags_names:
            tags_query = (
                'SELECT CONCAT("%23", name, " - ", definition) FROM tags '
                'WHERE name=%s;'
            )
            cursor.execute(tags_query, (name,))
            try:
                result.append(next(cursor)[0])
            except StopIteration:
                break
        cursor.close()
        return '%0A'.join(result)

    def _get_tag_id(self, *tags_names):
        cursor = self.cnx.cursor()
        result = []
        for name in tags_names:
            tags_query = (
                'SELECT id FROM tags '
                'WHERE name=%s;'
            )
            cursor.execute(tags_query, (name,))
            try:
                result.append(next(cursor)[0])
            except StopIteration:
                break
        cursor.close()
        return '%0A'.join(result)

    def write(self, date, text, user_id, tags_names):
        cursor = self.cnx.cursor()
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
            add_message_tag = (
                'INSERT INTO messages_tags (message_id, tag_id) '
                'VALUES '
                '    (%s, %s);'
            )
            cursor.execute(add_message_tag, (message_id, tag_id))
        self.cnx.commit()
        cursor.close()
        return u'заметка {0} сохранена'.format(message_id)

    def write_tag(self, tag_name, tag_definition):
        cursor = self.cnx.cursor()
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
            self.cnx.commit()
            cursor.close()   

    def read_last(self, user_id):
        cursor = self.cnx.cursor()
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
        return text.replace('#', '%23')

    def read(self, user_id, message_id):
        cursor = self.cnx.cursor()
        text_query = (
            'SELECT text, user_id FROM messages '
            'WHERE id=%s;'
        )
        cursor.execute(text_query, (message_id,))
        try:
            text, owner_id = next(cursor)
        except StopIteration:
            cursor.close()
            return u'заметка {0} не найдена'.format(message_id)
        cursor.close()
        if user_id == owner_id:
            return text.replace('#', '%23')
        return (u'заметка {0} принадлежит другому '
                u'пользователю').format(message_id)

    def read_all(self, user_id):
        cursor = self.cnx.cursor()
        text_query = (
            'SELECT text FROM messages '
            'WHERE user_id=%s;'
        )
        cursor.execute(text_query, (user_id,))
        result = [row[0].replace('#', '%23') for row in cursor]
        cursor.close()
        return '%0A'.join(result)

    def read_tag(self, user_id, tag_name):
        cursor = self.cnx.cursor()
        text_query = (
            'SELECT text FROM messages '
            'JOIN messages_tags ON messages.id = messages_tags.message_id '
            'JOIN tags ON tags.id = messages_tags.tag_id '
            'WHERE user_id=%s AND tags.name=%s;'
        )
        cursor.execute(text_query, (user_id, tag_name))
        result = [row[0].replace('#', '%23') for row in cursor]
        cursor.close()
        return '%0A'.join(result)

    def tag_all(self):
        cursor = self.cnx.cursor()
        text_query = 'SELECT CONCAT("%23", name, "-", definition) FROM tags;'
        cursor.execute(text_query)
        result = [row[0] for row in cursor]
        cursor.close()
        return '%0A'.join(result)
