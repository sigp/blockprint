#!/usr/bin/env bash

cd ..
source ./venv/bin/activate
gunicorn --timeout 1800 api_server:app
