#!/usr/bin/env python

import base64
import socket
import hashlib
import threading

import time
import struct


HANDSHAKE = '''HTTP/1.1 101 Switching Protocols\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Accept: {key}
\r\n'''


MAGIC_KEY = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'


def generate_accept_token(key):

    key = key.strip() + MAGIC_KEY
    key_hashed = hashlib.sha1(key).digest()
    return base64.b64encode(key_hashed)

def split_handshake_request(request):

    request = request.strip().split('\r\n')[1:]
    return {line.split(':')[0]: line.split(':')[1] for line in request}



class WebSocket(object):

    def __init__(self, host, port):

        self.host = host
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(10)

        self.handshaken = False

        self.data = ''

        self.client, adress = self.socket.accept()

        self.handle()


    def handle(self):

        while True:
            if not self.handshaken:
                data = self.client.recv(255)
                data = data.decode('utf-8', 'ignore')
                self.do_handshake(data)
            else:
                msg = self.client.recv(4096)
                if msg.startswith('\x88\x80'): # Close frame
                    self.close(msg)
                else:
                    self.echo(msg)



    def do_handshake(self, request):

        request = split_handshake_request(request)
        key = generate_accept_token(request['Sec-WebSocket-Key'])
        origin = request['Sec-WebSocket-Origin'].strip()

        handshake = HANDSHAKE.format(key=key, origin=origin, host=self.host, port=self.port)

        self.handshaken = True

        self.client.send(handshake)


    def close(self, msg):

        frame = struct.pack('B', 0x80 | 0x8)
        frame += struct.pack('B', 0)

        self.client.send(frame)

        self.socket.close()



    def echo(self,  msg):

        self.client.send('\x00' + 'Test'.encode('utf-8') + '\xff')



if __name__ == '__main__':
    sock = WebSocket('127.0.0.1', 8086)
