from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/',     admin.site.urls),
    path('accounts/',  include('accounts.urls')),
    path('dashboard/', lambda request: redirect('accounts:dashboard')),
    path('',           lambda request: redirect('accounts:login')),
]