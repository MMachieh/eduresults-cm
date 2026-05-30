#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Render free tier doesn't support SSH/Shell, so we run these during the build
python create_admin.py
python seed_data.py
python seed_demo_extra.py
