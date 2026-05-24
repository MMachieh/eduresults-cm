from django.core.mail import send_mass_mail
from django.conf import settings
from school.models import Enrollment
from accounts.models import Parent

def notify_parents_sequence_published(sequence):
    """
    Sends an email notification to all parents whose children have results
    in the published sequence.
    """
    academic_year = sequence.term.academic_year
    
    # Get all students enrolled in this academic year
    enrollments = Enrollment.objects.filter(academic_year=academic_year).select_related('student')
    student_ids = [e.student.id for e in enrollments]
    
    # Find all parents linked to these students
    parents = Parent.objects.filter(students__id__in=student_ids).select_related('user').distinct()
    
    from_email = settings.DEFAULT_FROM_EMAIL
    if not from_email:
        return

    messages = []
    subject = f"Results Published: Sequence {sequence.name} - Term {sequence.term.name}"
    
    for parent in parents:
        if parent.user.email:
            # Find which of their children are relevant
            children = parent.students.filter(id__in=student_ids)
            child_names = ", ".join([child.user.get_full_name() for child in children])
            
            message = (
                f"Dear {parent.user.first_name},\n\n"
                f"The official results for Sequence {sequence.name} (Term {sequence.term.name}, {academic_year}) "
                f"have been published and are now available on the EduResults CM portal.\n\n"
                f"You can log in to view the detailed marks, averages, and class rankings for your child(ren): {child_names}.\n\n"
                f"Best regards,\n"
                f"School Administration"
            )
            messages.append((subject, message, from_email, [parent.user.email]))
            
    if messages:
        try:
            send_mass_mail(tuple(messages), fail_silently=True)
        except Exception:
            pass
