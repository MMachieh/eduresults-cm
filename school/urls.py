from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    path('admin/publish/', views.admin_publish_sequence, name='publish_sequence'),
]
