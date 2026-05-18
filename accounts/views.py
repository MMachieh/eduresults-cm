from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required


class RoleLoginView(LoginView):
    template_name = 'accounts/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_admin():   return '/dashboard/'
        if user.is_teacher(): return '/dashboard/'
        if user.is_student(): return '/dashboard/'
        if user.is_parent():  return '/dashboard/'
        return '/'


@login_required
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