import importlib
import os
import re
import sqlite3
import string
import urllib.parse
import http.client

from wsgiref.simple_server import make_server, demo_app
from wsgiref.headers import Headers

"""
https://www.youtube.com/watch?v=7kwnjoAJ2HQ&t=1559s
https://jacobian.github.io/pycon2017/#/45
"""


class NotFound(BaseException):
    pass


class Request:
    def __init__(self, environ):
        self.environ = environ

    @property
    def args(self):
        get_args = urllib.parse.parse_qs(self.environ['QUERY_STRING'])
        return {k: v[0] for k, v in get_args.items()}


class Response:
    def __init__(self, response=None, status=200, charset='utf-8',
                 content_type='text/html'):

        self.response = [] if response is None else response
        self.charset = charset
        self.headers = Headers()
        ctype = f'{content_type}; charset={charset})'
        self.headers.add_header('content-type', ctype)
        self._status = status

    @property
    def status(self):
        status_string = http.client.responses.get(self._status, 'UNKNOWN')
        return f'{self._status} {status_string}'

    def __iter__(self):
        for k in self.response:
            if isinstance(k, bytes):
                yield k
            else:
                yield k.encode(self.charset)


def request_response_application(function):
    def application(environ, start_response):
        module, app_name = os.environ['APP'].split(':')
        module = importlib.import_module(module)
        app = getattr(module, app_name)

        request = Request(environ)
        response = app(request)
        start_response(response.status, response.headers.items())
        return iter(response)

    return application


@request_response_application
def application(request):
    name = request.args.get('name', 'PyCon')
    return Response([
        '<doctype html>',
        '<html>',
        f'<head><title>Hello, {name}</title></head>',
        f'<body><h1>Hello, {name}!</body>',
        '</html>',
    ])


# def application(environ, start_response):
#     status = '200 OK'
#     headers = [('Content-Type', 'text/html; charset=utf8')]
#     start_response(status, headers)
#
#     query_string = urllib.parse.parse_qs(environ['QUERY_STRING'])
#     name = query_string.get('name', ['PyCon'])[0]
#
#     return [f'<h1>Hello, {name}!</h1>'.encode('utf-8')]

def application(environ, start_response):
    module = os.environ['APP']
    module = importlib.import_module(module)
    router = getattr(module, 'routes')

    try:
        request = Request(environ)
        callback, args = router.match(request.path)
        response = callback(request, *args)
    except NotFound:
        response = Response("<h1>Not found</h1>", status=404)

    start_response(response.status, response.headers.items())
    return iter(response)


class Router:
    def __init__(self):
        self.routing_table = []

    def add_route(self, pattern, callback):
        self.routing_table.append((pattern, callback))

    def match(self, path):
        for (pattern, callback) in self.routing_table:
            m = re.match(pattern, path)
            if m:
                return callback, m.groups()
        raise NotFound()


class TemplateResponse(Response):
    def __init__(self, template, context, **kwargs):
        super().__init__(**kwargs)
        self.template = template
        self.context = context

    def __iter__(self):
        template = string.Template(open(self.template).read())
        response = template.substitute(self.context)
        yield response.encode(self.charset)


class GreetingDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('greetings.sqlite')

    def get_and_increment_count(self, greeting, name):
        c = self.conn.cursor()
        c.execute("""SELECT greeting_count FROM greeting_counts 
                      WHERE greeting=? AND name=?""", [greeting, name])
        rows = c.fetchall()
        if rows:
            count = rows[0][0] + 1
            c.execute("""UPDATE greeting_counts 
                         SET greeting_count=? 
                         WHERE greeting=? AND name=?""", [count, greeting, name])
        else:
            count = 1
            c.execute("""INSERT INTO greeting_counts 
                         (greeting, name, greeting_count) 
                         VALUES (?, ?, 1)""", [greeting, name])

        self.conn.commit()
        return count


if __name__ == '__main__':
    with make_server('', 8080, application) as server:
        server.serve_forever()
