from django.db import models
from accounts.models import Student, Teacher
from school.models import Subject, Sequence


class Mark(models.Model):
    student  = models.ForeignKey(Student,  on_delete=models.CASCADE, related_name='marks')
    subject  = models.ForeignKey(Subject,  on_delete=models.CASCADE)
    sequence = models.ForeignKey(Sequence, on_delete=models.CASCADE, related_name='marks')
    teacher  = models.ForeignKey(Teacher,  on_delete=models.CASCADE,
                                 null=True, blank=True)
    value    = models.DecimalField(max_digits=4, decimal_places=2,
                                   null=True, blank=True)   # null = absent
    remark   = models.CharField(max_length=200, blank=True)
    entered_at = models.DateTimeField(auto_now=True)

    @property
    def weighted(self):
        if self.value is None:
            return None
        return round(self.value * self.subject.coefficient, 2)

    def is_absent(self):
        return self.value is None

    def __str__(self):
        val = "AB" if self.is_absent() else str(self.value)
        return f"{self.student} | {self.subject} | Seq {self.sequence.name} → {val}"

    class Meta:
        unique_together = ['student', 'subject', 'sequence']
        ordering = ['sequence', 'student']