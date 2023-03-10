from django.urls import path

from . import views

app_name = 'create'

urlpatterns = [
    path('', views.create, name='create'),
    path('add/', views.add, name='add'),
]
