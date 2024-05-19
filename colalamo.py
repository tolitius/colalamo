import http.server
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

def copilot(token, prompt):

    if shtoken.is_token_expired(token):
        print("refreshing the token...")
        token = shtoken.refresh_token()

    headers = {**(HEADERS | COPILOT_CHAT_HEADERS),
               'authorization': f'Bearer {token}'}

    ## TODO: take this dict as an argument
    ##       most of these need to have default values
    req = {'intent': True,
           'model': 'gpt-4',
           'n': 1,
           'stream': False,
           'temperature': 0.1,
           'messages': [{'content': prompt, 'role': 'user'}],
           'top_p': 1}

    try:
        print("asking... sit tight")
        resp = requests.post(GITHUB_COPILOT_CHAT_COMPLETIONS_URL,
                             headers=headers,
                             json=req)

        if resp.status_code != 200:
            print(f"error: response status code {resp.status_code}")
            print(f"reason: {resp.reason}")
            print(f"response text: {resp.text}")
            return ''

        try:
            parsed = resp.json()
            reply = parsed.get('choices')[0].get('message').get('content')
            return reply

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Error parsing JSON: {str(e)}")
            print(f"Response text: {resp.text}")
            return ''

    except requests.exceptions.ConnectionError as e:
        print(f"connection error: {str(e)}")
        return ''

def main():
    token = shtoken.refresh_token()
    # print(f"token: {token}")
    prompt = "write a user story for a chatbot that can help with code completion"
    completion = copilot(token, prompt)
    print(f"completion: {completion}")

if __name__ == '__main__':
    main()
