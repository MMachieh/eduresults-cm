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
        from school.models import Sequence, Enrollment
        from marks.services import compute_sequence_average, get_student_rank
        student = user.student_profile
        latest_seq = Sequence.objects.filter(is_published=True).order_by('-id').first()
        latest_avg = latest_rank = latest_total = None
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
        })
    if user.is_parent():
        from school.models import Sequence
        parent = user.parent_profile
        children = parent.students.select_related('user').all()
        published_sequences = Sequence.objects.filter(is_published=True).count()
        return render(request, 'accounts/dashboard_parent.html', {
            'children': children,
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
            student = Student.objects.get(matricule=matricule)

            parent = Parent.objects.create(
                user=user,
                phone_number=form.cleaned_data.get('phone_number')
            )
            parent.students.add(student)

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


def error_400(request, exception):
    return render(request, 'errors/400.html', status=400)

def error_403(request, exception):
    return render(request, 'errors/403.html', status=403)

def error_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def error_500(request):
    return render(request, 'errors/500.html', status=500)
