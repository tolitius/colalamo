#!/bin/bash

if [ "$#" -lt 1 ]; then
    echo "usage: $0 <prompt> [<file>]"
    exit 1
fi

prompt=$1
file=$2

# if file argument is not provided
if [ -z "$file" ]; then

    curl -X POST -H "Content-Type: application/json" -d "[{\"role\": \"user\", \"content\": \"$prompt\"}]" http://localhost:4242/ask
    exit 0
else

    if [ ! -f "$file" ]; then
        echo "file $file does not exist"
        exit 1
    fi

    cat $file | jq --arg prompt "$prompt" -Rs '[{"role": "user", "content": ($prompt + " " + .)}]' | curl -X POST -H "Content-Type: application/json" -d @- http://localhost:4242/ask

    exit 0
fi
