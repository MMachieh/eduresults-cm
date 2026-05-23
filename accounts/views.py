from django.shortcuts import render, redirect
from django.contrib.auth import logout, login
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from .forms import ParentRegistrationForm, CustomAuthenticationForm
from .models import Parent, Student
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
        return render(request, 'accounts/dashboard_admin.html')
    if user.is_teacher():
        return render(request, 'accounts/dashboard_teacher.html')
    if user.is_student():
        return render(request, 'accounts/dashboard_student.html')
    if user.is_parent():
        return render(request, 'accounts/dashboard_parent.html')
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
            user.save()
            
            matricule = form.cleaned_data.get('student_matricule')
            student = Student.objects.get(matricule=matricule)
            
            parent = Parent.objects.create(
                user=user,
                phone_number=form.cleaned_data.get('phone_number')
            )
            parent.students.add(student)
            
            login(request, user)
            return redirect('/accounts/dashboard/')
    else:
        form = ParentRegistrationForm()
    return render(request, 'accounts/register_parent.html', {'form': form})

def error_400(request, exception):
    return render(request, 'errors/400.html', status=400)

def error_403(request, exception):
    return render(request, 'errors/403.html', status=403)

def error_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def error_500(request):
    return render(request, 'errors/500.html', status=500)