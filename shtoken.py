import http.server
import requests
import json
import time
import sys
import os

from config import (
    GITHUB_DEVICE_CODE_URL,
    GITHUB_ACCESS_TOKEN_URL,
    GITHUB_COPILOT_TOKEN_URL,
    HEADERS,
    CLIENT_ID,
    DEVICE_CODE_DATA_TEMPLATE,
    ACCESS_TOKEN_DATA_TEMPLATE,
    WAIT_AUTH_MAX_RETRIES as MAX_RETRIES,
    WAIT_AUTH_RETRY_INTERVAL as RETRY_INTERVAL,
    TOKEN_FILE
)

def is_token_expired(token):

    pairs = token.split(';')
    token_dict = {}

    for pair in pairs:
        key, value = pair.split('=')
        token_dict[key] = value

    if 'exp' in token_dict:
        expiration_timestamp = int(token_dict['exp'])

        current_timestamp = int(time.time())

        if current_timestamp >= expiration_timestamp:
            return True
        else:
            return False
    else:
        return True


def read_token_from_file(token_file):

    if os.path.isfile(token_file):
        try:
            with open(token_file, 'r') as file:
                token = file.read().strip()
                return token
        except IOError as e:
            print(f"could not read token file: {e}")
            return None
    else:
        print(f"don't see a token file: {token_file}")
        return None

def wait_for_access_token(device_code):

    retry_count = 0

    while retry_count < MAX_RETRIES:

        time.sleep(RETRY_INTERVAL)
        retry_count += 1

        resp = requests.post(GITHUB_ACCESS_TOKEN_URL,
                             headers = HEADERS,
                             data = ACCESS_TOKEN_DATA_TEMPLATE.format(CLIENT_ID,
                                                                      device_code))

        parsed = resp.json()

        if 'access_token' in parsed:
            return parsed['access_token']

        elif 'error' in parsed:

            error_message = parsed['error']

            if error_message == 'authorization_pending':
                print('waiting for user authorization...')
            elif error_message == 'slow_down':
                print('rate limit exceeded. waiting for a minute before retrying...')
                time.sleep(60)
            else:
                print(f'error: {error_message}')
                break
        else:
            print('unexpected response format')
            break

    print('maximum retries exceeded. failed to obtain access token.')
    return None

# create github copilot access token
# record the token in a file

def create_access_token(token_file):

    resp = requests.post(GITHUB_DEVICE_CODE_URL,
                         headers = HEADERS,
                         data = DEVICE_CODE_DATA_TEMPLATE.format(CLIENT_ID))

    parsed = resp.json()
    device_code = parsed.get('device_code')
    user_code = parsed.get('user_code')
    verification_uri = parsed.get('verification_uri')

    print(f'browse to {verification_uri} and enter this code "{user_code}" to authenticate')

    access_token = wait_for_access_token(device_code)

    with open(token_file, 'w') as f:
        f.write(access_token)

    return access_token

def refresh_token(token_file=None):

    if token_file is None:
        token_file = os.path.expanduser(TOKEN_FILE)

    access_token = read_token_from_file(token_file)

    if access_token is None:
        access_token = create_access_token(token_file)

    headers = {**HEADERS,
               'authorization': f'token {access_token}'}

    try:
        response = requests.get(GITHUB_COPILOT_TOKEN_URL,
                                headers = headers)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"could not call copilot token referesh API due to: {e}")
        return None

    try:
        parsed = response.json()
        token = parsed.get('token')

        if token is None:
            print("could not extract the token from the API response")
            return None

        return token

    except json.JSONDecodeError:
        print("could not parse the API response as JSON")
        return None
