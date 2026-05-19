from decimal import Decimal
from django.db.models import Sum, F, Q
from .models import Mark
from school.models import Enrollment

def get_student_marks(student, sequence):
    """Return all marks for a student in a specific sequence."""
    return Mark.objects.filter(student=student, sequence=sequence).select_related('subject')

def compute_sequence_average(student, sequence):
    """
    Computes the weighted average for a student in a sequence.
    Absent marks are treated as 0 for computation.
    Returns (average, total_coeff, passed_subjects, total_subjects)
    """
    marks = get_student_marks(student, sequence)
    if not marks.exists():
        return None, 0, 0, 0
    
    total_weighted = Decimal('0.00')
    total_coeff = 0
    passed = 0
    
    for mark in marks:
        coeff = mark.subject.coefficient
        total_coeff += coeff
        val = mark.value if mark.value is not None else Decimal('0.00')
        total_weighted += val * coeff
        
        if val >= Decimal('10.00'):
            passed += 1
            
    if total_coeff == 0:
        return None, 0, 0, len(marks)
        
    avg = total_weighted / total_coeff
    return round(avg, 2), total_coeff, passed, len(marks)

def compute_class_ranking(class_group, sequence):
    """
    Computes the average for all students in a class for a sequence
    and returns a sorted list of dictionaries with their ranks.
    """
    enrollments = Enrollment.objects.filter(
        class_group=class_group, 
        academic_year=sequence.term.academic_year
    ).select_related('student__user')
    
    results = []
    for enrollment in enrollments:
        avg, _, _, _ = compute_sequence_average(enrollment.student, sequence)
        if avg is not None:
            results.append({
                'student': enrollment.student,
                'average': avg
            })
            
    # Sort descending by average
    results.sort(key=lambda x: x['average'], reverse=True)
    
    # Assign ranks (handling ties)
    current_rank = 1
    for i, res in enumerate(results):
        if i > 0 and res['average'] == results[i-1]['average']:
            res['rank'] = results[i-1]['rank']
        else:
            res['rank'] = current_rank
        current_rank += 1
        
    return results

def get_student_rank(student, class_group, sequence):
    """Gets the rank of a specific student in their class."""
    ranking = compute_class_ranking(class_group, sequence)
    for res in ranking:
        if res['student'] == student:
            return res['rank'], len(ranking)
    return None, len(ranking)
