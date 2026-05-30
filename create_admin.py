import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduresults_cm.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()
if not User.objects.filter(username='admin').exists():
    admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'mywebapp')
    print("Admin user created successfully.")
else:
    admin_user = User.objects.get(username='admin')
    admin_user.set_password('mywebapp')
    admin_user.save()
    print("Admin user already exists. Password reset to default.")
