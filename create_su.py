import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'boysfoundation.settings')  # <-- REPLACE 'myproject' WITH YOUR ACTUAL DJANGO PROJECT NAME
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Set details for your superuser
USERNAME = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
EMAIL = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
PASSWORD = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'AdminPassword123!')

if not User.objects.filter(username=USERNAME).exists():
    User.objects.create_superuser(username=USERNAME, email=EMAIL, password=PASSWORD)
    print(f"Superuser '{USERNAME}' created successfully!")
else:
    print(f"Superuser '{USERNAME}' already exists.")