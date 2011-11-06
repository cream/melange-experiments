#!/usr/bin/env python

import sys
import time
import signal
import base64
import socket
import hashlib
from select import select
from threading import Thread

from utils import decode, encode, Opcode


HANDSHAKE = '''HTTP/1.1 101 Switching Protocols\r
Upgrade: websocket\r
Connection: Upgrade\r
Sec-WebSocket-Accept: {key}\r\n\r\n'''


MAGIC_KEY = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

OP_CLOSE = 8


def generate_accept_token(key):

    key = key.strip() + MAGIC_KEY
    key_hashed = hashlib.sha1(key).digest()
    return base64.b64encode(key_hashed)

def split_handshake_request(request):

    request = request.strip().split('\r\n')[1:]
    return {line.split(':')[0]: line.split(':')[1] for line in request}



class WebSocket(object):

    def __init__(self, client, host, port):

        self.client = client
        self.host = host
        self.port = port

        self.handshaken = False
        self.closed = False
        self.data = ''


    def read(self):

        if not self.handshaken:
            data = self.client.recv(1024)
            self.do_handshake(data)
        else:
            self.data += self.client.recv(1024)

            res = decode(self.data)
            if res['remaining'] == 0:
                self.data = ''

            if res['data']:
                self.onmessage(res['data'])

            if res['opcode'] == Opcode.CLOSE:
                self.close()


    def onmessage(self, msg):

        print 'Got message: {0}'.format(msg)

        try:
           msg = encode(str(int(msg)+1), opcode=Opcode.TEXT)
           self.client.send(msg)
        except ValueError:
            pass

    def do_handshake(self, request):

        request = split_handshake_request(request)

        key = generate_accept_token(request['Sec-WebSocket-Key'])
        origin = request['Sec-WebSocket-Origin'].strip()
        handshake = HANDSHAKE.format(key=key, origin=origin, host=self.host, port=self.port)

        self.handshaken = True
        self.client.send(handshake)



    def close(self):

        self.send_close()
        self.closed = True


    def send_close(self):

        buf = encode('', opcode=Opcode.CLOSE)
        self.client.send(buf)




class WebSocketServer(object):

    def __init__(self, host, port):

        self.host = host
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((host, port))

        self.connections = {}
        self.listeners = [self.socket]
        self.running = True

    def listen(self):

        self.socket.listen(5)
        while self.running:
            rlist, wlist, xlist = select(self.listeners, [], self.listeners, 1)
            for ready in rlist:
                if ready == self.socket:
                    client, address = self.socket.accept()
                    fileno = client.fileno()
                    self.listeners.append(fileno)
                    self.connections[fileno] = WebSocket(client, self.host, self.port)
                else:
                    client = self.connections[ready].client
                    if self.connections[ready].closed:
                        print 'Closing socket...'
                        self.listeners.remove(client.fileno())
                        client.close()
                    else:
                        fileno = client.fileno()
                        self.connections[fileno].read()

            for failed in xlist:
                if failed == self.socket:
                    print 'Socket broke'
                    for fileno, conn in self.connections:
                        conn.close()
                    self.running = False




if __name__ == '__main__':

    server = WebSocketServer('localhost', 8080)
    server_thread = Thread(target=server.listen)
    server_thread.start()

    def signal_handler(signal, frame):
        print 'Exiting...'
        server.running = False
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
    while True:
        time.sleep(100)
