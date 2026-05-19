from django.contrib import admin
from .models import AcademicYear, Term, Sequence, Class, Subject, TeacherAssignment, Enrollment


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('label', 'start_date', 'end_date', 'is_active')


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'academic_year', 'name')


@admin.register(Sequence)
class SequenceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'term', 'name', 'is_published')
    list_filter  = ('is_published',)


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'level', 'suffix', 'academic_year', 'class_teacher')
    list_filter  = ('academic_year', 'level')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display    = ('name', 'coefficient', 'language')
    filter_horizontal = ('classes',)


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'class_group', 'academic_year')
    list_filter  = ('academic_year',)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_group', 'academic_year')
    list_filter  = ('academic_year',)