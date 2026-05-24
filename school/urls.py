from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    path('admin/publish/', views.admin_publish_sequence, name='publish_sequence'),
    path('structure/', views.school_structure, name='structure'),
    path('academic-years/', views.manage_academic_years, name='academic_years'),
    path('academic-years/<int:year_id>/set-active/', views.set_active_year, name='set_active_year'),
    path('classes/', views.manage_classes, name='classes'),
    path('subjects/', views.manage_subjects, name='subjects'),
    path('enrollments/', views.manage_enrollments, name='enrollments'),
    path('assignments/', views.manage_assignments, name='assignments'),
]
