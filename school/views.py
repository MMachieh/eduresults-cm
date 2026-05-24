from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import role_required
from .models import Sequence, AcademicYear, Term, Class, Subject, TeacherAssignment, Enrollment
from notifications.services import notify_parents_sequence_published
import datetime


@login_required
@role_required('admin')
def admin_publish_sequence(request):
    sequences = Sequence.objects.all().select_related('term__academic_year').order_by(
        '-term__academic_year__start_date', 'term', 'name'
    )

    if request.method == 'POST':
        sequence_id = request.POST.get('sequence')
        action = request.POST.get('action')

        if sequence_id:
            try:
                sequence_id = int(sequence_id)
            except ValueError:
                messages.error(request, "Invalid sequence ID.")
                return redirect('school:publish_sequence')

            sequence = get_object_or_404(Sequence, id=sequence_id)
            if action == 'publish':
                sequence.is_published = True
                sequence.save()
                messages.success(request, f"{sequence} published. Marks are locked and visible to students/parents.")
                notify_parents_sequence_published(sequence)
            elif action == 'unpublish':
                sequence.is_published = False
                sequence.save()
                messages.warning(request, f"{sequence} unpublished. Marks can be edited again.")

            return redirect('school:publish_sequence')

    return render(request, 'school/publish_sequence.html', {'sequences': sequences})


# ─── School Structure ────────────────────────────────────────────────────────

@login_required
@role_required('admin')
def school_structure(request):
    """Overview hub for school configuration."""
    academic_years = AcademicYear.objects.all().prefetch_related('terms__sequences', 'classes')
    subjects = Subject.objects.all().order_by('name')
    active_year = AcademicYear.objects.filter(is_active=True).first()
    classes = Class.objects.filter(academic_year=active_year).select_related(
        'academic_year', 'class_teacher__user'
    ).prefetch_related('subjects') if active_year else []
    return render(request, 'school/structure.html', {
        'academic_years': academic_years,
        'subjects': subjects,
        'classes': classes,
        'active_year': active_year,
    })


# ── Academic Year ──────────────────────────────────────────────────────────

@login_required
@role_required('admin')
def manage_academic_years(request):
    if request.method == 'POST':
        label = request.POST.get('label', '').strip()
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'
        if label and start and end:
            try:
                ay, created = AcademicYear.objects.get_or_create(label=label, defaults={
                    'start_date': start, 'end_date': end, 'is_active': is_active
                })
                if created:
                    if is_active:
                        ay.is_active = True
                        ay.save()
                    # Auto-create 3 terms and 6 sequences
                    for t in ['1', '2', '3']:
                        term, _ = Term.objects.get_or_create(academic_year=ay, name=t)
                        for s in ['1', '2']:
                            Sequence.objects.get_or_create(term=term, name=s)
                    messages.success(request, f"Academic year {label} created with 3 terms and 6 sequences.")
                else:
                    messages.warning(request, f"Academic year '{label}' already exists.")
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "All fields are required.")
        return redirect('school:academic_years')

    years = AcademicYear.objects.all().prefetch_related('terms__sequences').order_by('-start_date')
    return render(request, 'school/academic_years.html', {'years': years})


@login_required
@role_required('admin')
def set_active_year(request, year_id):
    if request.method == 'POST':
        ay = get_object_or_404(AcademicYear, id=year_id)
        ay.is_active = True
        ay.save()
        messages.success(request, f"{ay.label} is now the active academic year.")
    return redirect('school:academic_years')


# ── Classes ────────────────────────────────────────────────────────────────

@login_required
@role_required('admin')
def manage_classes(request):
    if request.method == 'POST':
        ay_id = request.POST.get('academic_year')
        level = request.POST.get('level', '').strip()
        suffix = request.POST.get('suffix', '').strip()
        teacher_id = request.POST.get('class_teacher') or None
        if ay_id and level:
            try:
                ay = get_object_or_404(AcademicYear, id=int(ay_id))
                teacher = None
                if teacher_id:
                    from accounts.models import Teacher
                    teacher = Teacher.objects.filter(id=int(teacher_id)).first()
                cls, created = Class.objects.get_or_create(
                    academic_year=ay, level=level, suffix=suffix,
                    defaults={'class_teacher': teacher}
                )
                if created:
                    messages.success(request, f"Class {cls} created.")
                else:
                    messages.warning(request, f"Class {cls} already exists.")
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "Academic year and level are required.")
        return redirect('school:classes')

    from accounts.models import Teacher
    classes = Class.objects.all().select_related(
        'academic_year', 'class_teacher__user'
    ).prefetch_related('enrollments__student__user').order_by(
        '-academic_year__start_date', 'level', 'suffix'
    )
    years = AcademicYear.objects.all().order_by('-start_date')
    teachers = Teacher.objects.all().select_related('user').order_by('user__last_name')
    from school.models import CLASS_LEVELS
    return render(request, 'school/classes.html', {
        'classes': classes,
        'years': years,
        'teachers': teachers,
        'class_levels': CLASS_LEVELS,
    })


# ── Subjects ───────────────────────────────────────────────────────────────

@login_required
@role_required('admin')
def manage_subjects(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        coeff = request.POST.get('coefficient', 1)
        lang = request.POST.get('language', 'english')
        class_ids = request.POST.getlist('classes')
        if name:
            try:
                subj, created = Subject.objects.get_or_create(name=name, defaults={
                    'coefficient': int(coeff), 'language': lang
                })
                if not created:
                    subj.coefficient = int(coeff)
                    subj.language = lang
                    subj.save()
                if class_ids:
                    classes = Class.objects.filter(id__in=[int(x) for x in class_ids])
                    subj.classes.add(*classes)
                messages.success(request, f"Subject '{name}' {'created' if created else 'updated'}.")
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "Subject name is required.")
        return redirect('school:subjects')

    subjects = Subject.objects.all().prefetch_related('classes__academic_year').order_by('name')
    classes = Class.objects.all().select_related('academic_year').order_by('-academic_year__start_date', 'level')
    return render(request, 'school/subjects.html', {
        'subjects': subjects,
        'classes': classes,
    })


# ── Enrollments ────────────────────────────────────────────────────────────

@login_required
@role_required('admin')
def manage_enrollments(request):
    from accounts.models import Student
    if request.method == 'POST':
        student_id = request.POST.get('student')
        class_id = request.POST.get('class_group')
        ay_id = request.POST.get('academic_year')
        if student_id and class_id and ay_id:
            try:
                student = get_object_or_404(Student, id=int(student_id))
                cls = get_object_or_404(Class, id=int(class_id))
                ay = get_object_or_404(AcademicYear, id=int(ay_id))
                enr, created = Enrollment.objects.get_or_create(
                    student=student, academic_year=ay,
                    defaults={'class_group': cls}
                )
                if created:
                    messages.success(request, f"{student} enrolled in {cls}.")
                else:
                    messages.warning(request, f"{student} is already enrolled in {enr.class_group} for this academic year.")
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "All fields are required.")
        return redirect('school:enrollments')

    enrollments = Enrollment.objects.all().select_related(
        'student__user', 'class_group', 'academic_year'
    ).order_by('-academic_year__start_date', 'class_group__level', 'student__user__last_name')
    students = Student.objects.select_related('user').order_by('user__last_name')
    classes = Class.objects.select_related('academic_year').order_by('-academic_year__start_date', 'level')
    years = AcademicYear.objects.all().order_by('-start_date')
    return render(request, 'school/enrollments.html', {
        'enrollments': enrollments,
        'students': students,
        'classes': classes,
        'years': years,
    })


# ── Teacher Assignments ─────────────────────────────────────────────────────

@login_required
@role_required('admin')
def manage_assignments(request):
    from accounts.models import Teacher
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher')
        subject_id = request.POST.get('subject')
        class_id = request.POST.get('class_group')
        ay_id = request.POST.get('academic_year')
        if teacher_id and subject_id and class_id and ay_id:
            try:
                teacher = get_object_or_404(Teacher, id=int(teacher_id))
                subject = get_object_or_404(Subject, id=int(subject_id))
                cls = get_object_or_404(Class, id=int(class_id))
                ay = get_object_or_404(AcademicYear, id=int(ay_id))
                asgn, created = TeacherAssignment.objects.get_or_create(
                    teacher=teacher, subject=subject, class_group=cls, academic_year=ay
                )
                if created:
                    messages.success(request, f"Assigned {teacher} to {subject.name} / {cls}.")
                else:
                    messages.warning(request, "This assignment already exists.")
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
            messages.error(request, "All fields are required.")
        return redirect('school:assignments')

    assignments = TeacherAssignment.objects.all().select_related(
        'teacher__user', 'subject', 'class_group', 'academic_year'
    ).order_by('-academic_year__start_date', 'class_group__level', 'subject__name')
    teachers = Teacher.objects.select_related('user').order_by('user__last_name')
    subjects = Subject.objects.all().order_by('name')
    classes = Class.objects.select_related('academic_year').order_by('-academic_year__start_date', 'level')
    years = AcademicYear.objects.all().order_by('-start_date')
    return render(request, 'school/assignments.html', {
        'assignments': assignments,
        'teachers': teachers,
        'subjects': subjects,
        'classes': classes,
        'years': years,
    })
