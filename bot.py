from __future__ import print_function
import json
import pprint
import os
import socket
import ssl
import sys
import re
from time import sleep


from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class Message:
    def __init__(
        self, update_id, user_id,
        date, text
    ):
        self.id = update_id
        self.user = user_id
        self.date = date
        self.text = text


class Telebot:
    HOST = 'api.telegram.org'
    PORT = 443
    BASE_CMD = ('GET /bot{0}/getUpdates?offset={1}&allowed_updates=["message"] HTTP/1.1\r\n'
                'Host: api.telegram.org\r\n'
                'Connection: close\r\n\r\n')

    def __init__(self, bot_id):
        self.id = bot_id
        self.offset = ''

    def _connect(self, host, port):
        mysock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            mysock.connect((host, port))
        except socket.error as err:
            print('Socket error: {0}'.format(err))
            sys.exit(1)
        context = ssl.create_default_context()
        return context.wrap_socket(mysock, server_hostname=host)

    def _check_updates(self):
        mysock = self._connect(self.HOST, self.PORT)
        cmd = self.BASE_CMD.format(self.id, self.offset)
        try:
            mysock.send(cmd.encode())
        except socket.error as err:
            print('Socket error: {0}'.format(err))
        response = b''
        while True:
            try:
                data = mysock.recv(512)
            except socket.error as err:
                print('Socket error: {0}'.format(err))
            response += data
            if not data:
                break
        mysock.close()
        http_response = str(response.decode())
        status = re.match(r'HTTP/1.1 (\d+) (.+)\s', http_response)
        status_code, status_description = status.groups()
        if not 200 <= int(status_code) <= 299:
            raise Exception('Error: {0} {1}'.format(status_code, status_description))
        pos = http_response.find('\r\n\r\n')
        data_dict = json.loads(http_response[pos:])
        try:
            self.offset = int(data_dict['result'][-1][u'update_id']) + 1
        except IndexError:
            pass
        except KeyError:
            pass
        return data_dict

    def _parse(self, data):
        if not data.get('ok'):
            description = data.get('description')
            return description
        result = data.get('result')
        messages = []
        for update in result:
            update_id = update.get('update_id')
            message = update.get('message')
            user_id = message['from']['id']
            date = message.get('date')
            text = message.get('text')
            messages.append(Message(
                update_id=update_id,
                user_id=user_id,
                date= date,
                text=text
                )
            )
        return messages

    def take_updates(self):
        data = self._check_updates()
        return self._parse(data)

bot = Telebot(os.environ.get('BOT_ID'))
for i in range(3):
    pprint.pprint(bot.take_updates())
    print(bot.offset)
    sleep(15)