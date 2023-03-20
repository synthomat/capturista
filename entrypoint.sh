#!/bin/sh

# install dependencies (idempotent)
playwright install chromium
playwright install-deps

gunicorn --bind 0.0.0.0 'capturista:create_app()'