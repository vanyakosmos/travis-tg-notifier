#!/usr/bin/env bash

python manage.py collectstatic
python manage.py migrate
python manage.py setwebhook
