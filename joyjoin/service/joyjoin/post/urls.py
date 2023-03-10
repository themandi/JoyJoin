from django.urls import path
from . import views

app_name = 'post'

urlpatterns = [

    path('<int:post_id>/', views.post, name='post'),
    path('reply/', views.reply, name="reply"),
    path('change_sorting/', views.change_sorting, name="change_sorting"),
    path('vote_comment/<int:option>/', views.vote_comment, name='vote_comment'),
    path('vote/<int:option>/', views.vote, name='vote'),
    path('display_new_posts/', views.display_new_posts, name='display_new_posts'),
]
