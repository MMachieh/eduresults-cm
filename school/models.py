from django.db import models
from accounts.models import Teacher, Student


CLASS_LEVELS = [
    ('Form 1',      'Form 1'),
    ('Form 2',      'Form 2'),
    ('Form 3',      'Form 3'),
    ('Form 4',      'Form 4'),
    ('Form 5',      'Form 5'),
    ('Lower Sixth', 'Lower Sixth'),
    ('Upper Sixth', 'Upper Sixth'),
]


class AcademicYear(models.Model):
    label      = models.CharField(max_length=20)        # e.g. "2024-2025"
    start_date = models.DateField()
    end_date   = models.DateField()
    is_active  = models.BooleanField(default=False)

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        # Only one academic year can be active at a time
        if self.is_active:
            AcademicYear.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-start_date']


class Term(models.Model):
    TERM_CHOICES = [('1', 'Term 1'), ('2', 'Term 2'), ('3', 'Term 3')]
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE,
                                      related_name='terms')
    name          = models.CharField(max_length=1, choices=TERM_CHOICES)

    def __str__(self):
        return f"Term {self.name} — {self.academic_year}"

    class Meta:
        ordering = ['academic_year', 'name']
        unique_together = ['academic_year', 'name']


class Sequence(models.Model):
    SEQ_CHOICES = [('1', 'Sequence 1'), ('2', 'Sequence 2')]
    term         = models.ForeignKey(Term, on_delete=models.CASCADE,
                                     related_name='sequences')
    name         = models.CharField(max_length=1, choices=SEQ_CHOICES)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return f"Seq {self.name} · {self.term}"

    class Meta:
        ordering = ['term', 'name']
        unique_together = ['term', 'name']


class Class(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE,
                                      related_name='classes')
    level         = models.CharField(max_length=20, choices=CLASS_LEVELS)
    suffix        = models.CharField(max_length=3, blank=True)   # e.g. "A", "B"
    class_teacher = models.ForeignKey(Teacher, null=True, blank=True,
                                      on_delete=models.SET_NULL,
                                      related_name='class_teacher_of')

    def __str__(self):
        return f"{self.level}{' ' + self.suffix if self.suffix else ''} ({self.academic_year})"

    class Meta:
        ordering = ['academic_year', 'level', 'suffix']
        verbose_name_plural = 'Classes'


class Subject(models.Model):
    LANGUAGE_CHOICES = [
        ('english',   'English'),
        ('french',    'French'),
        ('bilingual', 'Bilingual'),
    ]
    name        = models.CharField(max_length=100)
    coefficient = models.PositiveIntegerField(default=1)
    language    = models.CharField(max_length=10, choices=LANGUAGE_CHOICES,
                                   default='english')
    classes     = models.ManyToManyField(Class, related_name='subjects', blank=True)

    def __str__(self):
        return f"{self.name} (coeff. {self.coefficient})"

    class Meta:
        ordering = ['name']


class TeacherAssignment(models.Model):
    teacher       = models.ForeignKey(Teacher, on_delete=models.CASCADE,
                                      related_name='assignments')
    subject       = models.ForeignKey(Subject, on_delete=models.CASCADE)
    class_group   = models.ForeignKey(Class, on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.teacher} → {self.subject} / {self.class_group}"

    class Meta:
        unique_together = ['teacher', 'subject', 'class_group', 'academic_year']


class Enrollment(models.Model):
    student       = models.ForeignKey(Student, on_delete=models.CASCADE,
                                      related_name='enrollments')
    class_group   = models.ForeignKey(Class, on_delete=models.CASCADE,
                                      related_name='enrollments')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student} → {self.class_group}"

    class Meta:
        unique_together = ['student', 'academic_year']