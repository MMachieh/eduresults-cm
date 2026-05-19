from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/',     admin.site.urls),
    path('accounts/',  include('accounts.urls')),
    path('marks/',     include('marks.urls')),
    path('school/',    include('school.urls')),
    path('reports/',   include('reports.urls')),
    path('dashboard/', lambda request: redirect('accounts:dashboard')),
    path('',           lambda request: redirect('accounts:login')),
]

handler403 = 'accounts.views.error_403'
handler404 = 'accounts.views.error_404'
handler500 = 'accounts.views.error_500'