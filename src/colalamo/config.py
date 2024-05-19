CLIENT_ID = 'Iv1.b507a08c87ecfe98'

HEADERS = {
    'accept': 'application/json',
    'editor-version': 'Neovim/0.9.5',
    'editor-plugin-version': 'CopilotChat.nvim/2.0.0',
    'content-type': 'application/json',
    'user-agent': 'CopilotChat.nvim/2.0.0',
    # 'accept-encoding': 'gzip,deflate,br'
    }

COPILOT_CHAT_HEADERS = {
        'copilot-integration-id': 'vscode-chat',
        'openai-organization':    'github-copilot',
        'openai-intent':          'conversation-panel'}

TOKEN_FILE = '.copilot-token'

## create a new device code

GITHUB_DEVICE_CODE_URL = 'https://github.com/login/device/code'
DEVICE_CODE_DATA_TEMPLATE = '{{"client_id":"{}","scope":"read:user"}}'

## waiting for a user to authenticate

GITHUB_ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token'
ACCESS_TOKEN_DATA_TEMPLATE = '{{"client_id":"{}","device_code":"{}","grant_type":"urn:ietf:params:oauth:grant-type:device_code"}}'

WAIT_AUTH_MAX_RETRIES = 6
WAIT_AUTH_RETRY_INTERVAL = 8

GITHUB_COPILOT_TOKEN_URL = 'https://api.github.com/copilot_internal/v2/token'
GITHUB_COPILOT_CHAT_COMPLETIONS_URL = 'https://api.githubcopilot.com/chat/completions'
