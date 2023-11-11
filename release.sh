#!/bin/sh

set -e
python manage.py migrate_schemas --shared
python manage.py migrate
python manage.py bulk_create_roles
python manage.py init_admin
python manage.py init_public_client

