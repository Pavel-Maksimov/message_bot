import os
from time import sleep

from bot import MessageParser, Telebot
from db_connector import DbConnector


DB = {
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'host': os.environ.get('DB_HOST'),
    'database': os.environ.get('DB_NAME')
}


def main():
    bot = Telebot(os.environ.get('BOT_ID'))
    conn = DbConnector(**DB)

    COMMANDS = {
        'start': conn.add_user,
        'read_last': conn.read_last,
        'read': conn.read,
        'read_all': conn.read_all,
        'read_tag': conn.read_tag,
        'write': conn.write,
        'write_tag': conn.write_tag,
        'tag': conn.tag,
        'tag_all': conn.tag_all
    }

    while True:
        messages = bot.take_updates()
        print('messages:', messages)
        for message in messages:
            print('message:', message)
            parser = MessageParser()
            command = parser.parse(message)
            if not command:
                continue
            if command.text in COMMANDS:
                result = COMMANDS[command.text](**command.params)
                if result:
                    bot.send_reply(user_id=message.user_id, reply=result)
        sleep(10)


if __name__ == '__main__':
    main()