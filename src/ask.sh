#!/bin/bash

if [ "$#" -lt 1 ]; then
    echo "usage: $0 <prompt> [<file>]"
    exit 1
fi

prompt=$1
file=$2

## TODO: take it as an argument
port=4242

# if file argument is not provided
if [ -z "$file" ]; then

    curl -sX POST -H "Content-Type: application/json" -d "{\"messages\": [{\"role\": \"user\", \"content\": \"$prompt\"}]}" http://localhost:$port/ask
    exit 0
else

    if [ ! -f "$file" ]; then
        echo "file $file does not exist"
        exit 1
    fi

    cat $file | jq --arg prompt "$prompt" -Rs '{"messages": [{"role": "user", "content": ($prompt + " " + .)}]}' | curl -sX POST -H "Content-Type: application/json" -d @- http://localhost:$port/ask

    exit 0
fi
