from django.urls import path

from . import views

app_name = 'sec'

urlpatterns = [
    path('<str:section_name>/', views.section, name='section'),
    path('<str:section_name>/tags/', views.tags, name='tags'),
    path('join/<str:section_name>/', views.join, name='join'),
    path('leave/<str:section_name>/', views.leave, name='leave'),
    path('<str:section_name>/preferences/',
         views.preferences, name='preferences'),
    path('<str:section_name>/update_punctation/',
         views.update_punctation, name='update_punctation'),
]
