from django.urls import path

from . import views

app_name = 'register'

urlpatterns = [
    path('', views.register, name='register'),
    path('complete/', views.complete, name='complete'),
    path('is_login_unused/', views.is_login_unused, name='is_login_unused'),
    path('is_password_uncommon/', views.is_password_uncommon, name='is_password_uncommon'),
    path('is_age_ok/', views.is_age_ok, name='is_age_ok'),
]
