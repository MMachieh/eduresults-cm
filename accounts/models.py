from django.contrib.auth.models import AbstractUser
from django.db import models
import os
import uuid
from django.core.exceptions import ValidationError
from PIL import Image

def student_photo_upload_to(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('students/', filename)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin',   'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent',  'Parent'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    def is_admin(self):   return self.role == 'admin'
    def is_teacher(self): return self.role == 'teacher'
    def is_student(self): return self.role == 'student'
    def is_parent(self):  return self.role == 'parent'

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


class Student(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE,
                                      related_name='student_profile')
    matricule  = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    photo      = models.ImageField(upload_to=student_photo_upload_to, null=True, blank=True)

    def clean(self):
        super().clean()
        if self.photo:
            try:
                img = Image.open(self.photo)
                img.verify()
                if img.format.lower() not in ['jpeg', 'jpg', 'png']:
                    raise ValidationError({'photo': 'Only JPEG and PNG formats are allowed.'})
            except Exception as e:
                raise ValidationError({'photo': 'Invalid image file.'})

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.matricule})"


class Teacher(models.Model):
    user           = models.OneToOneField(User, on_delete=models.CASCADE,
                                          related_name='teacher_profile')
    staff_id       = models.CharField(max_length=20, unique=True)
    specialisation = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.staff_id})"


class Parent(models.Model):
    user         = models.OneToOneField(User, on_delete=models.CASCADE,
                                        related_name='parent_profile')
    phone_number = models.CharField(max_length=20, blank=True)
    students     = models.ManyToManyField(Student, related_name='parents', blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()}"