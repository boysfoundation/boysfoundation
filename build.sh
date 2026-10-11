#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install packages
pip install -r requirements.txt

# Run database migrations on Supabase
python manage.py migrate

# Create the admin account
python create_su.py