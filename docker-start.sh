#!/bin/sh

if [[ -n ${SECRET_KEY} ]]; then
    /app/secret_key.py ensure secret_key.txt
    export SECRET_KEY="$(cat secret_key.txt)"
fi

django-admin migrate

exec uwsgi --ini /app/uwsgi.ini
