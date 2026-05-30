import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduresults_cm.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'mywebapp')
    print("Admin user created successfully.")
else:
    print("Admin user already exists.")
