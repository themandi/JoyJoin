from django.urls import path

from . import views
from sec.views import preferences

app_name = 'all'

urlpatterns = [
    path('', views.all, name='all'),
    path('404devel', views.error_404, name='404devel'),
    path('preferences', preferences, name='preferences'),
]
