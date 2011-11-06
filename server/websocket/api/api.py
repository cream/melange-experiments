from websocket import WebSocket, run
import json


class ApiWebSocket(WebSocket):

    def __init__(self, client, host, port):

        WebSocket.__init__(self, client, host, port)


    def onmessage(self, data):

        print 'Received:', data
        data = json.loads(data)

        if data['type'] == 'init':
            self.api = Api.apis[data['name']]()
            methods = self.api.get_methods()
            msg = {'type': 'init', 'methods': methods}
            self.send(json.dumps(msg))
        elif data['type'] == 'call':
            res = getattr(self.api, data['method'])(**data['args'])
            msg = {'type': 'call', 'id': data['id'], 'data': res}
            self.send(json.dumps(msg))



class Api(object):

    apis = {}

    @staticmethod
    def expose(func):
        func.exposed = True
        return func


    @staticmethod
    def register(name):
        def wrap(c):
            c.name = name
            Api.apis[name] = c
            return c
        return wrap


    def get_methods(self):
        methods = []
        for attr in dir(self):
            if hasattr(getattr(self, attr), 'exposed'):
                methods.append(attr)
        return methods



# Example API


import urllib
from contextlib import closing
from lxml.etree import parse as parse_xml


CURRENT_URL = 'http://api.wunderground.com/auto/wui/geo/WXCurrentObXML/index.xml?query={0}'


@Api.register('weather')
class Weather(Api):


    @Api.expose
    def get_temperature(self, location):

        print
        print location
        print

        current_url = CURRENT_URL.format(location)
        with closing(urllib.urlopen(current_url)) as file_handle:
            current_data = parse_xml(file_handle)

        return {'temperature': current_data.find('temp_c').text, 'location': location}



if __name__ == '__main__':
    run(ApiWebSocket)
