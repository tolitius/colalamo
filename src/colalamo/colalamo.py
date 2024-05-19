import sys
import os
import time
import argparse

import json

import http.server
import socketserver
import requests

from . import shtoken

from .config import (
    HEADERS,
    COPILOT_CHAT_HEADERS,
    GITHUB_COPILOT_CHAT_COMPLETIONS_URL
)

class Copilot():

    def __init__(self):
        self.token = shtoken.refresh_token()

    def ask(self,
            messages,
            intent=True,
            stream=False,
            reply_as_is=False,   # return the response as is, without any post-processing | parsing
            model='gpt-4',
            n=1,
            temperature=0.1,
            top_p=1):

        if shtoken.is_token_expired(self.token):
            print("refreshing the token...")
            self.token = shtoken.refresh_token()

        headers = {**(HEADERS | COPILOT_CHAT_HEADERS),
                   'authorization': f'Bearer {self.token}'}

        ## proxy all the args copilot
        req = locals()
        req.pop('self', None)
        req.pop('reply_as_is', None)

        try:
            resp = requests.post(GITHUB_COPILOT_CHAT_COMPLETIONS_URL,
                                 headers = headers,
                                 json = req)

            if resp.status_code != 200:
                return {'status': resp.status_code,
                        'text': {'reason': resp.reason,
                                 'text': resp.text}}

            try:

                if reply_as_is:
                    return resp.json()

                parsed = resp.json()

                return {'status': 200,
                        'text': {'reply': self.parse_reply(parsed),
                                 'usage': self.parse_usage(parsed)}}

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                problem = f"error parsing JSON: {str(e)} of this response: {resp.text}"
                return {'status': 400,
                        'text': problem + ", response: " + response.text}

        except requests.exceptions.ConnectionError as e:
            problem = f"connection error: {str(e)}"
            return {'status': 400,
                    'text': problem}

    def parse_reply(self, reply):
        return reply.get('choices')[0].get('message').get('content')

    def parse_usage(self, reply):
        return reply.get('usage')

class ColalamoHandler(http.server.SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        self.copilot = kwargs.pop('copilot')
        super().__init__(*args, **kwargs)

    def do_POST(self):

        if self.path == '/ask':

            print("asking... sit tight")

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                prompt = json.loads(post_data.decode('utf-8'))

                response = self.copilot.ask(**prompt)

            except json.JSONDecodeError:
                response = {
                    "status": "error",
                    "text": "invalid JSON data"
                }
                self.send_response(400)
            else:
                self.send_response(response['status'])

            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response['text']).encode('utf-8'))

        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"not found => I'm not listening to this endpoint")

class Colalamo():

    def __init__(self, port=4242):
        self.port = port

    def start(self):

        handler = lambda *args, **kwargs: ColalamoHandler(*args,
                                                          **kwargs,
                                                          copilot = Copilot())
        with socketserver.TCPServer(("", self.port), handler) as httpd:
            print(f"colalamo is listening on 0.0.0.0:{self.port}")
            print(f"ask away at \"/ask\"")
            print(f"""example: curl http://localhost:{self.port}/ask -X POST -d '{{"messages": [{{"role": "user", "content": "explain how multi-head attention work"}}]}}'""")
            httpd.serve_forever()




def parse_arguments():
    description = """
colalamo is a proxy server that sends custom requests via GitHub Copilot to its backing LLMs

usage: colalamo [--port PORT]
"""
    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter, usage=argparse.SUPPRESS)

    parser.add_argument("-p", "--port", type=int, default=4242, help="colalamo will listen on this port number (default: 4242)")

    return parser.parse_args()

def main():

    args = parse_arguments()
    port = args.port

    colalamo = Colalamo(port)
    colalamo.start()

    # prompt = "write a user story for a landing page that has three charts with totals, under each chart that is a ui grid with data"
    # copilot = Copilot()

    # answer = copilot.ask({'messages': [{'content': prompt,
    #                                     'role': 'user'}]})

    # print(f"answer: {answer}")

if __name__ == '__main__':
    main()
