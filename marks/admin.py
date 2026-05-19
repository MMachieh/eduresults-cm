from django.contrib import admin
from .models import Mark


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'sequence', 'value', 'teacher', 'entered_at')
    list_filter  = ('sequence', 'subject')
    search_fields = ('student__matricule', 'student__user__last_name')