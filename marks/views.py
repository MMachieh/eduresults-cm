from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from school.models import TeacherAssignment, Sequence, Enrollment
from .models import Mark
from .forms import MarkEntryForm
from django.forms import modelformset_factory
from django.contrib import messages
from .services import compute_sequence_average, get_student_rank
from accounts.models import Student

@login_required
@role_required(['teacher'])
def select_assignment(request):
    teacher = request.user.teacher_profile
    assignments = TeacherAssignment.objects.filter(teacher=teacher).select_related('subject', 'class_group', 'academic_year')
    sequences = Sequence.objects.all().select_related('term__academic_year')
    
    if request.method == 'POST':
        assignment_id = request.POST.get('assignment')
        sequence_id = request.POST.get('sequence')
        if assignment_id and sequence_id:
            return redirect('marks:mark_entry_sheet', assignment_id=assignment_id, sequence_id=sequence_id)
            
    return render(request, 'marks/select_assignment.html', {
        'assignments': assignments,
        'sequences': sequences
    })

@login_required
@role_required(['teacher'])
def mark_entry_sheet(request, assignment_id, sequence_id):
    assignment = get_object_or_404(TeacherAssignment, id=assignment_id, teacher=request.user.teacher_profile)
    sequence = get_object_or_404(Sequence, id=sequence_id)
    
    enrollments = Enrollment.objects.filter(class_group=assignment.class_group, academic_year=assignment.academic_year)
    students = [e.student for e in enrollments]
    
    # Ensure a Mark object exists for every student for this assignment and sequence
    for student in students:
        Mark.objects.get_or_create(
            student=student,
            subject=assignment.subject,
            sequence=sequence,
            defaults={'teacher': assignment.teacher}
        )
        
    MarkFormSet = modelformset_factory(Mark, form=MarkEntryForm, extra=0)
    queryset = Mark.objects.filter(subject=assignment.subject, sequence=sequence, student__in=students).select_related('student__user').order_by('student__user__last_name', 'student__user__first_name')
    
    if request.method == 'POST':
        if sequence.is_published:
            messages.error(request, "This sequence is published and marks are locked.")
            return redirect('marks:select_assignment')
            
        formset = MarkFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Marks saved successfully.")
            return redirect('marks:mark_entry_sheet', assignment_id=assignment_id, sequence_id=sequence_id)
    else:
        formset = MarkFormSet(queryset=queryset)
        
    return render(request, 'marks/mark_entry_sheet.html', {
        'assignment': assignment,
        'sequence': sequence,
        'formset': formset,
        'is_locked': sequence.is_published
    })

@login_required
@role_required(['student'])
def student_results_view(request):
    student = request.user.student_profile
    sequences = Sequence.objects.filter(is_published=True).select_related('term__academic_year')
    
    sequence_id = request.GET.get('sequence')
    selected_sequence = None
    results = None
    avg = None
    rank = None
    
    if sequence_id:
        selected_sequence = get_object_or_404(Sequence, id=sequence_id, is_published=True)
        marks = Mark.objects.filter(student=student, sequence=selected_sequence).select_related('subject')
        avg, _, _, _ = compute_sequence_average(student, selected_sequence)
        
        enrollment = Enrollment.objects.filter(student=student, academic_year=selected_sequence.term.academic_year).first()
        if enrollment:
            rank, _ = get_student_rank(student, enrollment.class_group, selected_sequence)
            
        results = marks
        
    return render(request, 'marks/student_results.html', {
        'student': student,
        'sequences': sequences,
        'selected_sequence': selected_sequence,
        'results': results,
        'average': avg,
        'rank': rank
    })

@login_required
@role_required(['parent'])
def parent_results_view(request):
    parent = request.user.parent_profile
    students = parent.students.all()
    
    student_id = request.GET.get('student')
    sequence_id = request.GET.get('sequence')
    
    selected_student = None
    selected_sequence = None
    results = None
    avg = None
    rank = None
    
    sequences = Sequence.objects.filter(is_published=True).select_related('term__academic_year')
    
    if student_id:
        selected_student = get_object_or_404(students, id=student_id)
        if sequence_id:
            selected_sequence = get_object_or_404(Sequence, id=sequence_id, is_published=True)
            marks = Mark.objects.filter(student=selected_student, sequence=selected_sequence).select_related('subject')
            avg, _, _, _ = compute_sequence_average(selected_student, selected_sequence)
            
            enrollment = Enrollment.objects.filter(student=selected_student, academic_year=selected_sequence.term.academic_year).first()
            if enrollment:
                rank, _ = get_student_rank(selected_student, enrollment.class_group, selected_sequence)
                
            results = marks
            
    return render(request, 'marks/parent_results.html', {
        'students': students,
        'sequences': sequences,
        'selected_student': selected_student,
        'selected_sequence': selected_sequence,
        'results': results,
        'average': avg,
        'rank': rank
    })

