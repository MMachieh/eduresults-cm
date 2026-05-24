from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',              views.RoleLoginView.as_view(), name='login'),
    path('logout/',             views.logout_view,             name='logout'),
    path('dashboard/',          views.dashboard,               name='dashboard'),
    path('register/parent/',    views.parent_register,         name='parent_register'),
    path('pending-approval/',   views.pending_approval,        name='pending_approval'),
    path('approve-parent/<int:user_id>/', views.approve_parent, name='approve_parent'),
    path('reject-parent/<int:user_id>/',  views.reject_parent,  name='reject_parent'),

    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]
