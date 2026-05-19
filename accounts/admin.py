from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Student, Teacher, Parent


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter   = ('role', 'is_active')
    fieldsets     = UserAdmin.fieldsets + (
        ('Role', {'fields': ('role',)}),
    )


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display  = ('matricule', 'user', 'date_of_birth')
    search_fields = ('matricule', 'user__first_name', 'user__last_name')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display  = ('staff_id', 'user', 'specialisation')
    search_fields = ('staff_id', 'user__first_name', 'user__last_name')


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display  = ('user', 'phone_number')
    filter_horizontal = ('students',)