#!/bin/sh

gunicorn --bind 0.0.0.0 'capturista:create_app()'