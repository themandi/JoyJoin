from django.urls import path

from . import views

app_name = 'user'

urlpatterns = [
    path('<str:username>/', views.user, name='user'),
]
