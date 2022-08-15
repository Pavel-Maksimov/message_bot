# -*- coding: utf-8 -*-
from __future__ import print_function
import datetime
import json
import os
import re
import socket
import ssl
import sys

from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class Message:
    def __init__(self, id, user_id, date, text):
        self.id = id
        self.user_id = user_id
        self.date = date
        self.text = text


class Command():
    def __init__(self, text, params):
        self.text = text
        self.params = params


class MessageParser:
    def _extract_tags(self, text):
        return re.findall(r'\#(\S+)', text)

    def parse(self, message):
        match = re.match(r'\/(\w+)\s?(.*\s?)?', message.text)
        if match:
            command, tail = match.groups()
            if command == 'start':
                params = {
                    'user_id': message.user_id,
                    'date': message.date
                }
            elif command == 'write':
                tags = self._extract_tags(tail)
                params = {
                    'user_id': message.user_id,
                    'date': message.date,
                    'text': tail,
                    'tags_names': tags
                }
            elif command == 'write_tag':
                tag_name, tag_definition = tail.split(' ', 1)
                params = {
                    'tag_name': tag_name,
                    'tag_definition': tag_definition
                }
            elif command == 'read_last':
                params = {
                    'user_id': message.user_id
                }
            elif command == 'read':
                params = {
                    'user_id': message.user_id,
                    'message_id': int(tail)
                }
            elif command == 'read_all':
                params = {
                    'user_id': message.user_id
                }
            elif command == 'read_tag':
                params = {
                    'user_id': message.user_id,
                    'tag_name': tail
                }
            elif command == 'tag':
                params = {
                    'tags_names': tail.split()
                }
            elif command == 'tag_all':
                params = {}
            return Command(text=command, params=params)



class Telebot:
    HOST = 'api.telegram.org'
    PORT = 443
    UPDATE_URL = ('GET /bot{0}/getUpdates?offset={1}&allowed_updates=["message"] HTTP/1.1\r\n'
                  'Host: api.telegram.org\r\n'
                  'Connection: close\r\n\r\n')
    SEND_URL = ('GET /bot{0}/sendMessage?chat_id={1}&text={2} HTTP/1.1\r\n'
                'Host: api.telegram.org\r\n'
                'Connection: close\r\n\r\n')

    def __init__(self, bot_id):
        self.id = bot_id
        self.offset = 289794988

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
        cmd = self.UPDATE_URL.format(self.id, self.offset)
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
        return data_dict

    def _parse(self, data):
        try:
            self.offset = int(data['result'][-1]['update_id']) + 1
        except IndexError:
            pass
        except KeyError:
            pass
        if not data.get('ok'):
            description = data.get('description')
            return description
        result = data.get('result')
        messages = []
        for update in result:
            update_id = update.get('update_id')
            message = update.get('message')
            user_id = message['from']['id']
            date = datetime.datetime.fromtimestamp(message.get('date'))
            text = message.get('text')
            messages.append(Message(
                id=update_id,
                user_id=user_id,
                date= date,
                text=text
                )
            )
        return messages

    def take_updates(self):
        data = self._check_updates()
        return self._parse(data)

    def send_reply(self, user_id, reply):
        mysock = self._connect(self.HOST, self.PORT)
        cmd = unicode(self.SEND_URL, 'utf-8').format(self.id, user_id, reply)
        try:
            mysock.send(cmd.encode('utf-8'))
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
