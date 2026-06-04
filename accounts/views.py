from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ParentRegistrationForm, CustomAuthenticationForm
from .models import User, Parent, Student, Teacher
from .decorators import role_required
from django_ratelimit.decorators import ratelimit


class RoleLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = CustomAuthenticationForm

    def get_success_url(self):
        user = self.request.user
        if user.is_admin():   return '/dashboard/'
        if user.is_teacher(): return '/dashboard/'
        if user.is_student(): return '/dashboard/'
        if user.is_parent():  return '/dashboard/'
        return '/'


@login_required
@role_required('admin', 'teacher', 'student', 'parent')
def dashboard(request):
    user = request.user
    if user.is_admin():
        from school.models import Class, Sequence
        pending_parents = User.objects.filter(role='parent', is_active=False).prefetch_related('parent_profile__students__user')
        context = {
            'total_students': Student.objects.count(),
            'total_teachers': Teacher.objects.count(),
            'total_classes': Class.objects.count(),
            'published_sequences': Sequence.objects.filter(is_published=True).count(),
            'pending_parents': pending_parents,
        }
        return render(request, 'accounts/dashboard_admin.html', context)
    if user.is_teacher():
        from school.models import TeacherAssignment, Sequence
        assignments = TeacherAssignment.objects.filter(
            teacher=user.teacher_profile
        ).select_related('subject', 'class_group', 'academic_year')
        published_sequences = Sequence.objects.filter(is_published=True).count()
        return render(request, 'accounts/dashboard_teacher.html', {
            'assignments': assignments,
            'published_sequences': published_sequences,
        })
    if user.is_student():
        from school.models import Sequence, Enrollment, AcademicYear
        from marks.services import compute_sequence_average, get_student_rank
        student = user.student_profile
        latest_seq = Sequence.objects.filter(is_published=True).order_by('-id').first()
        latest_avg = latest_rank = latest_total = None
        active_year = AcademicYear.objects.filter(is_active=True).first()
        current_enrollment = Enrollment.objects.filter(
            student=student, academic_year=active_year
        ).select_related('class_group').first() if active_year else None
        if latest_seq:
            latest_avg, _, _, _ = compute_sequence_average(student, latest_seq)
            enrollment = Enrollment.objects.filter(student=student, academic_year=latest_seq.term.academic_year).first()
            if enrollment and latest_avg is not None:
                latest_rank, latest_total = get_student_rank(student, enrollment.class_group, latest_seq)
        return render(request, 'accounts/dashboard_student.html', {
            'student': student,
            'latest_seq': latest_seq,
            'latest_avg': latest_avg,
            'latest_rank': latest_rank,
            'latest_total': latest_total,
            'current_enrollment': current_enrollment,
        })
    if user.is_parent():
        from school.models import Sequence, Enrollment, AcademicYear
        parent = user.parent_profile
        active_year = AcademicYear.objects.filter(is_active=True).first()
        children_with_class = []
        for child in parent.students.select_related('user').all():
            enr = Enrollment.objects.filter(
                student=child, academic_year=active_year
            ).select_related('class_group').first() if active_year else None
            children_with_class.append({'student': child, 'enrollment': enr})
        published_sequences = Sequence.objects.filter(is_published=True).count()
        return render(request, 'accounts/dashboard_parent.html', {
            'children_with_class': children_with_class,
            'published_sequences': published_sequences,
        })
    return redirect('accounts:login')


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


@ratelimit(key='ip', rate='5/h', block=True)
def parent_register(request):
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'parent'
            user.is_active = False  # Requires admin approval before login is possible
            user.save()

            matricule = form.cleaned_data.get('student_matricule')
            parent = Parent.objects.create(
                user=user,
                phone_number=form.cleaned_data.get('phone_number')
            )
            
            try:
                student = Student.objects.get(matricule=matricule)
                parent.students.add(student)
            except Student.DoesNotExist:
                pass

            return redirect('accounts:pending_approval')
    else:
        form = ParentRegistrationForm()
    return render(request, 'accounts/register_parent.html', {'form': form})


def pending_approval(request):
    return render(request, 'accounts/pending_approval.html')


@login_required
@role_required('admin')
def approve_parent(request, user_id):
    parent_user = get_object_or_404(User, id=user_id, role='parent', is_active=False)
    if request.method == 'POST':
        parent_user.is_active = True
        parent_user.save()
        messages.success(request, f"Account for {parent_user.get_full_name()} has been approved. They can now log in.")
    return redirect('accounts:dashboard')


@login_required
@role_required('admin')
def reject_parent(request, user_id):
    parent_user = get_object_or_404(User, id=user_id, role='parent', is_active=False)
    if request.method == 'POST':
        name = parent_user.get_full_name() or parent_user.username
        parent_user.delete()
        messages.warning(request, f"Registration request for {name} has been rejected and removed.")
    return redirect('accounts:dashboard')


@login_required
@role_required('admin')
def manage_students(request):
    from school.models import Enrollment
    q = request.GET.get('q', '').strip()
    students = Student.objects.select_related('user')
    if q:
        students = students.filter(
            user__first_name__icontains=q
        ) | Student.objects.filter(
            user__last_name__icontains=q
        ) | Student.objects.filter(
            matricule__icontains=q
        )
    students = students.order_by('user__last_name', 'user__first_name').distinct()
    # Attach current enrollment to each student
    result = []
    for stu in students:
        enr = Enrollment.objects.filter(student=stu).select_related(
            'class_group', 'academic_year'
        ).order_by('-academic_year__start_date').first()
        result.append({'student': stu, 'enrollment': enr})
    return render(request, 'accounts/manage/students.html', {
        'student_rows': result,
        'q': q,
        'total': students.count(),
    })


@login_required
@role_required('admin')
def manage_teachers(request):
    from school.models import TeacherAssignment
    q = request.GET.get('q', '').strip()
    teachers = Teacher.objects.select_related('user')
    if q:
        teachers = teachers.filter(
            user__first_name__icontains=q
        ) | Teacher.objects.filter(
            user__last_name__icontains=q
        ) | Teacher.objects.filter(
            staff_id__icontains=q
        )
    teachers = teachers.order_by('user__last_name', 'user__first_name').distinct()
    result = []
    for t in teachers:
        assignments = TeacherAssignment.objects.filter(teacher=t).select_related(
            'subject', 'class_group', 'academic_year'
        ).order_by('class_group__level')
        result.append({'teacher': t, 'assignments': assignments})
    return render(request, 'accounts/manage/teachers.html', {
        'teacher_rows': result,
        'q': q,
    })


@login_required
@role_required('admin')
def manage_parents(request):
    pending = User.objects.filter(role='parent', is_active=False).prefetch_related(
        'parent_profile__students__user'
    ).order_by('date_joined')
    active = User.objects.filter(role='parent', is_active=True).prefetch_related(
        'parent_profile__students__user'
    ).order_by('last_name', 'first_name')
    return render(request, 'accounts/manage/parents.html', {
        'pending_parents': pending,
        'active_parents': active,
    })


def error_400(request, exception):
    return render(request, 'errors/400.html', status=400)

def error_403(request, exception):
    return render(request, 'errors/403.html', status=403)

def error_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def error_500(request):
    return render(request, 'errors/500.html', status=500)
