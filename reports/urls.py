from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('hub/',                                              views.admin_report_hub,          name='admin_hub'),
    path('analytics/',                                        views.analytics,                 name='analytics'),
    path('online/<int:sequence_id>/',                         views.view_online_report_card,   name='online_report_card_self'),
    path('online/<int:sequence_id>/<int:student_id>/',        views.view_online_report_card,   name='online_report_card_student'),
    path('view/<int:sequence_id>/<int:student_id>/',          views.view_report_card_admin,    name='view_report_card'),
    path('pdf/<int:sequence_id>/<int:student_id>/',           views.download_pdf_report_card,  name='download_pdf'),
    path('zip/<int:sequence_id>/<int:class_id>/',             views.download_class_zip_reports, name='download_zip'),
    path('api/enrollments/',                                  views.api_get_enrollments,       name='api_enrollments'),
]
