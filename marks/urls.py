from django.urls import path
from . import views

app_name = 'marks'

urlpatterns = [
    path('teacher/assignments/',                                 views.select_assignment,   name='select_assignment'),
    path('teacher/entry/<int:assignment_id>/<int:sequence_id>/', views.mark_entry_sheet,   name='mark_entry_sheet'),
    path('teacher/class-summary/',                               views.class_summary,       name='class_summary'),
    path('student/results/',                                     views.student_results_view, name='student_results'),
    path('student/analytics/',                                   views.student_analytics,   name='student_analytics'),
    path('parent/results/',                                      views.parent_results_view, name='parent_results'),
]
