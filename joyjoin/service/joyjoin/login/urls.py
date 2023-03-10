from django.urls import path

from . import views

app_name = 'login'

urlpatterns = [
    path('', views.login, name='login'),
    path('verify/', views.verify, name='verify'),
    path('logout/', views.logout, name='logout'),
]
