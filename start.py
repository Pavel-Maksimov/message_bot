import os
from time import sleep

from bot import Telebot, parse_data
from db_connector import DbConnector, DB


def main():
    bot = Telebot(os.environ.get('BOT_ID'))
    DB['database'] = os.environ.get('DB_NAME')
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
        data = bot.check_updates()
        commands = parse_data(data)
        if len(commands) == 0:
            continue
        conn.open_connection()
        for command in commands:
            if command.text in COMMANDS:
                result = COMMANDS[command.text](**command.params)
                if result:
                    replies = result.split('%0A')
                    for reply in replies:
                        bot.send_reply(user_id=command.user_id, reply=reply)
        conn.close_connection()
            
        sleep(10)

if __name__ == '__main__':
    main()