import http.server
import socketserver
import requests
import json
import time
import sys
import os

import shtoken

from config import (
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
            reply_as_is=False, # return the response as is, without any post-processing | parsing
            model='gpt-4',
            n=1,
            temperature=0.1,
            top_p=1):

        if shtoken.is_token_expired(self.token):
            print("refreshing the token...")
            self.token = shtoken.refresh_token()

        headers = {**(HEADERS | COPILOT_CHAT_HEADERS),
                   'authorization': f'Bearer {self.token}'}

        req = {'intent': intent,
               'model': model,
               'n': n,
               'stream': stream,
               'temperature': temperature,
               'messages': messages,
               'top_p': top_p}

        try:
            resp = requests.post(GITHUB_COPILOT_CHAT_COMPLETIONS_URL,
                                 headers = headers,
                                 json = req)

            if resp.status_code != 200:
                print(f"error: response status code {resp.status_code}")
                print(f"reason: {resp.reason}")
                print(f"response text: {resp.text}")
                return ''

            try:

                if reply_as_is:
                    return resp.json()

                parsed = resp.json()

                return {'reply': self.parse_reply(parsed),
                        'usage': self.parse_usage(parsed)}

            except (json.JSONDecodeError, KeyError, IndexError) as e:
                print(f"Error parsing JSON: {str(e)}")
                print(f"Response text: {resp.text}")
                return ''

        except requests.exceptions.ConnectionError as e:
            print(f"connection error: {str(e)}")
            return ''

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

                ## TODO: it should take all the parameters
                response = self.copilot.ask(prompt)

            except json.JSONDecodeError:
                response = {
                    "status": "error",
                    "message": "invalid JSON data"
                }
                self.send_response(400)
            else:
                self.send_response(200)

            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

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
            print(f"ask away at 0.0.0.0:{self.port}/ask")
            httpd.serve_forever()

def main():

    colalamo = Colalamo()
    colalamo.start()

    # prompt = "write a user story for a landing page that has three charts with totals, under each chart that is a ui grid with data"
    # copilot = Copilot()

    # answer = copilot.ask([{'content': prompt,
    #                        'role': 'user'}])

    # print(f"answer: {answer}")

if __name__ == '__main__':
    main()
