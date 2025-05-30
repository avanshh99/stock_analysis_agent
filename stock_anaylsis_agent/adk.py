# adk.py - Minimal ADK implementation for the stock analysis project
from typing import Dict, Any, Callable
from dataclasses import dataclass

@dataclass
class Agent:
    subagents: Dict[str, Callable]

    def __init__(self):
        self.subagents = {}

    def register_subagent(self, name: str, func: Callable):
        self.subagents[name] = func

class web:
    class App:
        def __init__(self):
            self.routes = {}

        def route(self, path: str):
            def decorator(func):
                self.routes[path] = func
                return func
            return decorator

        def run(self, host='0.0.0.0', port=8080):
            from wsgiref.simple_server import make_server
            def app(environ, start_response):
                path = environ['PATH_INFO']
                if path in self.routes:
                    status = '200 OK'
                    response = self.routes[path]().encode()
                else:
                    status = '404 Not Found'
                    response = b'Not Found'
                start_response(status, [('Content-type', 'text/html')])
                return [response]
            print(f"Server running on {host}:{port}")
            make_server(host, port, app).serve_forever()