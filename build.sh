#!/usr/bin/env bash
set -e
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput

if [ -n "$DJANGO_ADMIN_USERNAME" ] && \
   [ -n "$DJANGO_ADMIN_EMAIL" ] && \
   [ -n "$DJANGO_ADMIN_PASSWORD" ]; then
    python manage.py create_admin
fi
