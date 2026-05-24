import io
import json
import zipfile
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from accounts.decorators import role_required
from school.models import Sequence, Class, Enrollment, AcademicYear
from accounts.models import Student, Teacher
from marks.models import Mark
from marks.services import compute_sequence_average, get_student_rank
from django.template.loader import get_template
from xhtml2pdf import pisa


def get_report_card_context(student, sequence):
    marks = Mark.objects.filter(student=student, sequence=sequence).select_related('subject', 'teacher__user')
    average, total_coeff, passed, total = compute_sequence_average(student, sequence)

    enrollment = Enrollment.objects.filter(student=student, academic_year=sequence.term.academic_year).first()
    rank = None
    if enrollment:
        rank, _ = get_student_rank(student, enrollment.class_group, sequence)

    return {
        'student': student,
        'sequence': sequence,
        'class_group': enrollment.class_group if enrollment else None,
        'marks': marks,
        'average': average,
        'total_coeff': total_coeff,
        'rank': rank,
        'is_pass': average is not None and average >= 10,
    }


@login_required
def view_online_report_card(request, sequence_id, student_id=None):
    sequence = get_object_or_404(Sequence, id=sequence_id, is_published=True)

    if student_id:
        student = get_object_or_404(Student, id=student_id)
        if request.user.is_parent():
            if not request.user.parent_profile.students.filter(id=student.id).exists():
                return HttpResponseForbidden("You are not authorized to view this report card.")
        elif not request.user.is_admin():
            return HttpResponseForbidden("You are not authorized to view this report card.")
    else:
        if not request.user.is_student():
            return HttpResponseForbidden("Student ID required.")
        student = request.user.student_profile

    context = get_report_card_context(student, sequence)
    return render(request, 'reports/online_report_card.html', context)


@login_required
@role_required('admin')
def download_pdf_report_card(request, sequence_id, student_id):
    sequence = get_object_or_404(Sequence, id=sequence_id, is_published=True)
    student = get_object_or_404(Student, id=student_id)

    context = get_report_card_context(student, sequence)

    template_path = 'reports/pdf_report_card.html'
    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    filename = f"Report_Card_{student.matricule}_{sequence.term.academic_year.label.replace('-', '_')}_Seq{sequence.name}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("PDF generation failed. Please contact the administrator.", status=500)
    return response


@login_required
@role_required('admin')
def download_class_zip_reports(request, sequence_id, class_id):
    sequence = get_object_or_404(Sequence, id=sequence_id, is_published=True)
    class_group = get_object_or_404(Class, id=class_id)

    enrollments = Enrollment.objects.filter(
        class_group=class_group,
        academic_year=sequence.term.academic_year
    ).select_related('student')

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        template = get_template('reports/pdf_report_card.html')
        for enrollment in enrollments:
            student = enrollment.student
            context = get_report_card_context(student, sequence)
            html = template.render(context)
            pdf_buffer = io.BytesIO()
            pisa.CreatePDF(html, dest=pdf_buffer)
            filename = f"{student.matricule}_{student.user.get_full_name().replace(' ', '_')}.pdf"
            zip_file.writestr(filename, pdf_buffer.getvalue())

    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    zip_filename = f"{class_group.level}_{class_group.suffix}_Seq{sequence.name}_Reports.zip"
    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
    return response


@login_required
@role_required('admin')
def view_report_card_admin(request, sequence_id, student_id):
    sequence = get_object_or_404(Sequence, id=sequence_id, is_published=True)
    student = get_object_or_404(Student, id=student_id)
    context = get_report_card_context(student, sequence)
    return render(request, 'reports/online_report_card.html', context)


@login_required
@role_required('admin')
def admin_report_hub(request):
    sequences = Sequence.objects.filter(is_published=True).select_related('term__academic_year')
    classes = Class.objects.all().select_related('academic_year')
    return render(request, 'reports/admin_report_hub.html', {
        'sequences': sequences,
        'classes': classes,
    })


@login_required
@role_required('admin')
def api_get_enrollments(request):
    ay_id = request.GET.get('academic_year')
    if not ay_id:
        return JsonResponse({'error': 'academic_year required'}, status=400)
    try:
        ay_id = int(ay_id)
    except ValueError:
        return JsonResponse({'error': 'invalid academic_year'}, status=400)

    try:
        enrollments = Enrollment.objects.filter(
            academic_year_id=ay_id
        ).select_related('student__user').values_list(
            'student_id', 'student__user__first_name',
            'student__user__last_name', 'student__matricule'
        ).distinct()

        data = {
            'enrollments': [
                {
                    'student_id': e[0],
                    'student_name': f"{e[1]} {e[2]}",
                    'matricule': e[3]
                }
                for e in enrollments
            ]
        }
        return JsonResponse(data)
    except AcademicYear.DoesNotExist:
        return JsonResponse({'error': 'Academic year not found'}, status=404)


@login_required
@role_required('student')
def student_report_cards(request):
    student = request.user.student_profile
    sequences = Sequence.objects.filter(is_published=True).select_related('term__academic_year').order_by(
        'term__academic_year__start_date', 'term__name', 'name'
    )
    from marks.services import compute_sequence_average, get_student_rank
    report_cards = []
    for seq in sequences:
        avg, _, _, _ = compute_sequence_average(student, seq)
        enrollment = Enrollment.objects.filter(student=student, academic_year=seq.term.academic_year).first()
        rank = total = None
        if enrollment:
            rank, total = get_student_rank(student, enrollment.class_group, seq)
        report_cards.append({
            'sequence': seq,
            'average': avg,
            'rank': rank,
            'total': total,
            'is_pass': avg is not None and avg >= 10,
        })
    return render(request, 'reports/student_report_cards.html', {
        'student': student,
        'report_cards': report_cards,
    })


@login_required
@role_required('parent')
def parent_report_cards(request):
    parent = request.user.parent_profile
    students = parent.students.select_related('user').all()
    student_id = request.GET.get('student')

    selected_student = None
    report_cards = []

    if student_id:
        try:
            selected_student = students.get(id=int(student_id))
        except (Student.DoesNotExist, ValueError):
            pass

    if selected_student:
        sequences = Sequence.objects.filter(is_published=True).select_related('term__academic_year').order_by(
            'term__academic_year__start_date', 'term__name', 'name'
        )
        from marks.services import compute_sequence_average, get_student_rank
        for seq in sequences:
            avg, _, _, _ = compute_sequence_average(selected_student, seq)
            enrollment = Enrollment.objects.filter(student=selected_student, academic_year=seq.term.academic_year).first()
            rank = total = None
            if enrollment:
                rank, total = get_student_rank(selected_student, enrollment.class_group, seq)
            report_cards.append({
                'sequence': seq,
                'average': avg,
                'rank': rank,
                'total': total,
                'is_pass': avg is not None and avg >= 10,
            })

    return render(request, 'reports/parent_report_cards.html', {
        'students': students,
        'selected_student': selected_student,
        'report_cards': report_cards,
    })


@login_required
@role_required('admin')
def analytics(request):
    sequences = Sequence.objects.filter(is_published=True).select_related('term__academic_year')
    classes = Class.objects.all().select_related('academic_year')

    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_classes = Class.objects.count()
    total_sequences = sequences.count()

    seq_id = request.GET.get('sequence')
    class_id = request.GET.get('class_id')

    chart_data = None
    class_stats = None
    selected_sequence = None
    selected_class = None
    ranking_data = []

    if seq_id and class_id:
        try:
            selected_sequence = Sequence.objects.get(id=int(seq_id), is_published=True)
            selected_class = Class.objects.get(id=int(class_id))
        except (Sequence.DoesNotExist, Class.DoesNotExist, ValueError):
            pass

    if selected_sequence and selected_class:
        enrollments = Enrollment.objects.filter(
            class_group=selected_class,
            academic_year=selected_sequence.term.academic_year
        ).select_related('student__user')

        students = [e.student for e in enrollments]
        total_in_class = len(students)

        student_avgs = []
        for student in students:
            avg, _, _, _ = compute_sequence_average(student, selected_sequence)
            student_avgs.append({
                'student': student,
                'average': float(avg) if avg is not None else 0,
                'passed': avg is not None and avg >= 10,
            })

        student_avgs.sort(key=lambda x: x['average'], reverse=True)
        for i, s in enumerate(student_avgs):
            s['rank'] = i + 1

        ranking_data = student_avgs[:10]
        passed_count = sum(1 for s in student_avgs if s['passed'])

        subjects = selected_class.subjects.all().order_by('name')
        subject_labels = []
        subject_averages = []
        for subject in subjects:
            marks = Mark.objects.filter(
                student__in=students,
                subject=subject,
                sequence=selected_sequence,
                value__isnull=False
            )
            if marks.exists():
                avg_val = marks.aggregate(avg=Avg('value'))['avg']
                subject_labels.append(subject.name)
                subject_averages.append(round(float(avg_val), 2))

        class_avg = round(
            sum(s['average'] for s in student_avgs) / len(student_avgs), 2
        ) if student_avgs else 0

        chart_data = {
            'subjects': subject_labels,
            'subject_averages': subject_averages,
            'pass_fail': [passed_count, total_in_class - passed_count],
        }

        class_stats = {
            'total': total_in_class,
            'passed': passed_count,
            'failed': total_in_class - passed_count,
            'class_average': class_avg,
        }

    return render(request, 'reports/analytics.html', {
        'sequences': sequences,
        'classes': classes,
        'selected_sequence': selected_sequence,
        'selected_class': selected_class,
        'chart_data': json.dumps(chart_data) if chart_data else None,
        'class_stats': class_stats,
        'ranking_data': ranking_data,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_sequences': total_sequences,
    })
