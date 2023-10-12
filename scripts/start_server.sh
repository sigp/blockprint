#!/usr/bin/env bash

cd ..
source ./venv/bin/activate
# Bind on localhost and the Docker network interface.
# This makes the server easily accessible to Docker containers without using --network=host.
gunicorn --timeout 1800 --bind 127.0.0.1 --bind 172.17.0.1 api_server:app
