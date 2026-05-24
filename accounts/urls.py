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

    # Password Change (for non-admin users)
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html', success_url='/accounts/password_change/done/'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),

    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]
