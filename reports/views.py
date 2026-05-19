import io
import zipfile
import json
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from school.models import Sequence, Class, Enrollment, AcademicYear
from accounts.models import Student
from marks.models import Mark
from marks.services import compute_sequence_average, get_student_rank
from django.template.loader import get_template
from xhtml2pdf import pisa

def get_report_card_context(student, sequence):
    """Helper to gather all data needed for a report card"""
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
    
    # Access control
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
@role_required(['admin'])
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
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

@login_required
@role_required(['admin'])
def download_class_zip_reports(request, sequence_id, class_id):
    sequence = get_object_or_404(Sequence, id=sequence_id, is_published=True)
    class_group = get_object_or_404(Class, id=class_id)
    
    enrollments = Enrollment.objects.filter(class_group=class_group, academic_year=sequence.term.academic_year).select_related('student')
    
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
@role_required(['admin'])
def view_report_card_admin(request, sequence_id, student_id):
    """Allow admin to view report card online before downloading"""
    sequence = get_object_or_404(Sequence, id=sequence_id, is_published=True)
    student = get_object_or_404(Student, id=student_id)
    
    context = get_report_card_context(student, sequence)
    return render(request, 'reports/online_report_card.html', context)

@login_required
@role_required(['admin'])
def admin_report_hub(request):
    sequences = Sequence.objects.filter(is_published=True).select_related('term__academic_year')
    classes = Class.objects.all().select_related('academic_year')
    
    return render(request, 'reports/admin_report_hub.html', {
        'sequences': sequences,
        'classes': classes,
    })

@login_required
@role_required(['admin'])
def api_get_enrollments(request):
    """API endpoint to get students for a given academic year"""
    ay_id = request.GET.get('academic_year')
    
    if not ay_id:
        return JsonResponse({'error': 'academic_year required'}, status=400)
    
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
