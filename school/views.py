from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.decorators import role_required
from accounts.models import Teacher, Student
from .models import (
    AcademicYear,
    Class,
    Enrollment,
    Sequence,
    Subject,
    TeacherAssignment,
    Term,
)
from notifications.services import notify_parents_sequence_published


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
                messages.success(request, f"{sequence} has been published successfully. Marks are now locked and visible to students/parents.")
                # Trigger email notification
                notify_parents_sequence_published(sequence)
            elif action == 'unpublish':
                sequence.is_published = False
                sequence.save()
                messages.warning(request, f"{sequence} has been unpublished. Marks are now hidden and can be edited.")
                
            return redirect('school:publish_sequence')
            
    return render(request, 'school/publish_sequence.html', {
        'sequences': sequences
    })

@login_required
@role_required('admin')
def school_structure(request):
    active_year = AcademicYear.objects.filter(is_active=True).first()
    classes = []
    if active_year:
        classes = Class.objects.filter(academic_year=active_year).prefetch_related('subjects', 'enrollments')

    return render(request, 'school/structure.html', {
        'active_year': active_year,
        'classes': classes,
    })

@login_required
@role_required('admin')
def manage_academic_years(request):
    years = AcademicYear.objects.prefetch_related('terms__sequences').all()

    if request.method == 'POST':
        label = request.POST.get('label', '').strip()
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = bool(request.POST.get('is_active'))

        if not label or not start_date or not end_date:
            messages.error(request, "Please fill in all required fields.")
        elif AcademicYear.objects.filter(label__iexact=label).exists():
            messages.error(request, "An academic year with that label already exists.")
        else:
            year = AcademicYear.objects.create(
                label=label,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active,
            )
            for term_name in ['1', '2', '3']:
                term = Term.objects.create(academic_year=year, name=term_name)
                Sequence.objects.bulk_create([
                    Sequence(term=term, name='1'),
                    Sequence(term=term, name='2'),
                ])
            messages.success(request, f"Academic year {year.label} created successfully.")
            return redirect('school:academic_years')

    return render(request, 'school/academic_years.html', {
        'years': years,
    })

@login_required
@role_required('admin')
def set_active_year(request, year_id):
    if request.method != 'POST':
        return redirect('school:academic_years')

    year = get_object_or_404(AcademicYear, pk=year_id)
    year.is_active = True
    year.save()
    messages.success(request, f"{year.label} is now the active academic year.")
    return redirect('school:academic_years')

@login_required
@role_required('admin')
def manage_classes(request):
    years = AcademicYear.objects.order_by('-start_date')
    class_levels = Class._meta.get_field('level').choices
    teachers = Teacher.objects.order_by('user__first_name', 'user__last_name')
    classes = Class.objects.select_related('academic_year', 'class_teacher').prefetch_related('subjects', 'enrollments').order_by('academic_year', 'level', 'suffix')

    if request.method == 'POST':
        academic_year_id = request.POST.get('academic_year')
        level = request.POST.get('level')
        suffix = request.POST.get('suffix', '').strip()
        class_teacher_id = request.POST.get('class_teacher')

        if not academic_year_id or not level:
            messages.error(request, "Academic year and class level are required.")
        else:
            academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
            class_teacher = None
            if class_teacher_id:
                class_teacher = get_object_or_404(Teacher, pk=class_teacher_id)

            Class.objects.create(
                academic_year=academic_year,
                level=level,
                suffix=suffix,
                class_teacher=class_teacher,
            )
            messages.success(request, "Class created successfully.")
            return redirect('school:classes')

    return render(request, 'school/classes.html', {
        'years': years,
        'class_levels': class_levels,
        'teachers': teachers,
        'classes': classes,
    })

@login_required
@role_required('admin')
def manage_subjects(request):
    classes = Class.objects.order_by('academic_year', 'level', 'suffix')
    subjects = Subject.objects.prefetch_related('classes').all()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        coefficient = request.POST.get('coefficient') or 1
        language = request.POST.get('language', 'english')
        class_ids = request.POST.getlist('classes')

        if not name:
            messages.error(request, "Subject name is required.")
        else:
            try:
                coefficient = int(coefficient)
            except (TypeError, ValueError):
                coefficient = 1

            subject = Subject.objects.filter(name__iexact=name).first()
            if not subject:
                subject = Subject.objects.create(
                    name=name,
                    coefficient=coefficient,
                    language=language,
                )
                messages.success(request, f"Subject '{name}' created successfully.")
            else:
                subject.coefficient = coefficient
                subject.language = language
                subject.save()
                messages.success(request, f"Subject '{subject.name}' updated successfully.")

            subject.classes.set(Class.objects.filter(pk__in=class_ids))
            return redirect('school:subjects')

    return render(request, 'school/subjects.html', {
        'classes': classes,
        'subjects': subjects,
    })

@login_required
@role_required('admin')
def manage_enrollments(request):
    years = AcademicYear.objects.order_by('-start_date')
    students = Student.objects.order_by('user__first_name', 'user__last_name')
    classes = Class.objects.select_related('academic_year').order_by('academic_year', 'level', 'suffix')
    enrollments = Enrollment.objects.select_related('student__user', 'class_group', 'academic_year').order_by('academic_year', 'class_group')

    if request.method == 'POST':
        academic_year_id = request.POST.get('academic_year')
        student_id = request.POST.get('student')
        class_group_id = request.POST.get('class_group')

        if not academic_year_id or not student_id or not class_group_id:
            messages.error(request, "All enrollment fields are required.")
        else:
            academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
            student = get_object_or_404(Student, pk=student_id)
            class_group = get_object_or_404(Class, pk=class_group_id)

            if class_group.academic_year_id != academic_year.id:
                messages.error(request, "The selected class does not belong to the selected academic year.")
            else:
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    class_group=class_group,
                    academic_year=academic_year,
                )
                if created:
                    messages.success(request, "Student enrolled successfully.")
                else:
                    messages.warning(request, "This student is already enrolled for the selected year and class.")
                return redirect('school:enrollments')

    return render(request, 'school/enrollments.html', {
        'years': years,
        'students': students,
        'classes': classes,
        'enrollments': enrollments,
    })

@login_required
@role_required('admin')
def manage_assignments(request):
    years = AcademicYear.objects.order_by('-start_date')
    teachers = Teacher.objects.order_by('user__first_name', 'user__last_name')
    subjects = Subject.objects.all()
    classes = Class.objects.order_by('academic_year', 'level', 'suffix')
    assignments = TeacherAssignment.objects.select_related('teacher__user', 'subject', 'class_group', 'academic_year').all()

    if request.method == 'POST':
        academic_year_id = request.POST.get('academic_year')
        teacher_id = request.POST.get('teacher')
        subject_id = request.POST.get('subject')
        class_group_id = request.POST.get('class_group')

        if not academic_year_id or not teacher_id or not subject_id or not class_group_id:
            messages.error(request, "All assignment fields are required.")
        else:
            academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
            teacher = get_object_or_404(Teacher, pk=teacher_id)
            subject = get_object_or_404(Subject, pk=subject_id)
            class_group = get_object_or_404(Class, pk=class_group_id)

            if class_group.academic_year_id != academic_year.id:
                messages.error(request, "The selected class does not belong to the selected academic year.")
            else:
                assignment, created = TeacherAssignment.objects.get_or_create(
                    teacher=teacher,
                    subject=subject,
                    class_group=class_group,
                    academic_year=academic_year,
                )
                if created:
                    messages.success(request, "Teacher assignment saved successfully.")
                else:
                    messages.warning(request, "That assignment already exists.")
                return redirect('school:assignments')

    return render(request, 'school/assignments.html', {
        'years': years,
        'teachers': teachers,
        'subjects': subjects,
        'classes': classes,
        'assignments': assignments,
    })
