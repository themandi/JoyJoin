from django.shortcuts import get_object_or_404, render

from common.context import set_common_context
from common.models import User
from common.activity import update_activity
from post.views import get_posts


def user(request, username):
    """ Jest to funkcja, która przedstawia stronę zawierającą profil użytkownika i jego dane

    Args:
        request(WSGIRequest):obiekt klasy WSGIRequest
        username(str):nazwa użytkownika, dla ktorej chcemy pobrać dane

    Returns:
        django.http.HtttpResponse:obiekt reprezentujący wyrenderowany widok 'user/user.html' z ustawionym kontekstem szablonu
    """
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])
    user = get_object_or_404(User, login=username)
    context['user'] = user
    request.session['list_of_displayed_posts'] = []
    context['posts_to_display'] = get_posts(request, user_name=username)
    return render(request, 'user/user.html', context)
