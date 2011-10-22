#!/usr/bin/env python

import base64
import socket
import hashlib
import threading

import time


HANDSHAKE = '''HTTP/1.1 101 Switching Protocols
Upgrade: WebSocket
Connection: Upgrade
Sec-WebSocket-Origin: {origin}
Sec-WebSocket-Accept: {key}
Sec-WebSocket-Location: ws://{host}:{port}/
Sec-WebSocket-Protocol: sample
Sec-Websocket-Version: 8'''


MAGIC_KEY = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

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


    def handle(self, client):

        if not self.handshaken:
            data = client.recv(255)
            data = data.decode('utf-8', 'ignore')
            print data
            self.do_handshake(client, data)
        else:
            print client.recv(10)
            print msg
            self.do_stuff(client, msg)



    def do_handshake(self, client, request):

        request = split_handshake_request(request)
        key = hashlib.sha1(request['Sec-WebSocket-Key'] + MAGIC_KEY).digest()
        key = base64.encodestring(key).strip()
        origin = request['Sec-WebSocket-Origin'].strip()

        handshake = HANDSHAKE.format(key=key, origin=origin, host=self.host, port=self.port)

        self.handshaken = True
        print handshake

        client.send(handshake)


    def do_stuff(self, msg):

        pass


    def loop(self):

        try:
            while True:
                client, adress = self.socket.accept()
                self.handle(client)
                threading.Thread(target=self.handle, args=(t,)).start()
        except KeyboardInterrupt:
            self.socket.close()


sock = WebSocket('127.0.0.1', 8092)

try:
    sock.loop()
except Exception:
    sock.socket.close()
