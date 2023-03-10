from django.shortcuts import get_object_or_404, redirect, render

from common.activity import update_activity
from common.context import set_common_context
from common.models import User, Post, Section, Tag, TagPunctation, Vote
from post.views import get_posts
from sec.comments import get_comments_list


def section(request, section_name):
    """ Jest to funkcja, która przedstawia stronę zawierającą sekcje.

    Sprawdza czy użytkownik jest w danej sekcji i czy może napisać w niej post.

    Args:
        request(WSGIRequest):obiekt klasy WSGIRequest
        section_name(str):nazwa sekcji, dla której chcemy pobrać posty

    Returns:
        django.http.HtttpResponse:obiekt reprezentujący wyrenderowany widok 'sec/sec.html' z ustawionym kontekstem szablonu
    """
    try:
        tag_name = request.GET['tag']
    except KeyError:
        tag_name = None

    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])
    context['current_section_name'] = request.session['current_section_name'] = section_name

    posts_to_display = []

    if section_name != 'all':
        current_section = get_object_or_404(Section, name=section_name)
        context['current_section'] = current_section
        context['this_is_the_all_view'] = False

        if context['current_user']:
            if current_section.users.filter(login=context['current_user'].login):
                context['current_user_in_current_section'] = True
            else:
                context['current_user_in_current_section'] = False
        else:
            context['current_user_in_current_section'] = False

        participants = list(current_section.users.all())
        participants.sort(key=lambda x: len(Post.objects.filter(author=x, section=current_section)), reverse=True)
    else:
        context['this_is_the_all_view'] = True
        posts_to_display = Post.objects.order_by('-creation_time')

        participants = list(User.objects.all())
        participants.sort(key=lambda x: len(Post.objects.filter(author=x)), reverse=True)

    selected_posts = posts_to_display
    posts_to_display = []

    for post in selected_posts:
        is_liked = False
        is_disliked = False
        if Vote.objects.filter(post=post, user=context['current_user'], reaction=1).exists():
            is_liked = True
        if Vote.objects.filter(post=post, user=context['current_user'], reaction=-1).exists():
            is_disliked = True

        comments_to_display = get_comments_list(post, context['current_user'])
        posts_to_display.append((post, post.count_votes(
            1), post.count_votes(-1), is_liked, is_disliked, comments_to_display))

    context['posts_to_display'] = posts_to_display
    context['this_is_section_view'] = True
    context['section_name'] = section_name
    context['tag_name'] = tag_name
    request.session['list_of_displayed_posts'] = []
    posts_to_display = get_posts(request,
                                 section_name, tag_name)

    context['participants'] = participants[0:5]

    if tag_name is not None and len(posts_to_display) == 0:
        return redirect("sec:section", section_name)
    else:
        context['posts_to_display'] = posts_to_display

    return render(request, 'sec/sec.html', context)


def tags(request, section_name):
    """ Jest to funkcja, która przedstawia stronę zawierającą tagi

    Args:
        request(WSGIRequest):obiekt klasy WSGIRequest
        section_name(str):nazwa sekcji, dla której chcemy pobrać posty

    Returns:
        django.http.HtttpResponse:obiekt reprezentujący wyrenderowany widok 'sec/tags.html' z ustawionym kontekstem szablonu
    """
    current_section = get_object_or_404(Section, name=section_name)
    request.session['current_section_name'] = section_name

    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])

    # dołącz popularność do tagów
    tags_to_display = []
    posts_in_this_section = Post.objects.filter(section=current_section)
    for tag in Tag.objects.filter(section=current_section):
        popularity = 0
        for post in posts_in_this_section:
            if tag in post.tags.all() or tag in post.implied_tags.all():
                popularity += 1
        tags_to_display.append(('a', tag, popularity))
    usertags = {}
    for post in posts_in_this_section:
        for usertag in post.user_tags_as_list():
            try:
                usertags[usertag] += 1
            except KeyError:
                usertags[usertag] = 1
    for usertag in usertags:
        tags_to_display.append(('u', usertag, usertags[usertag]))

    # posortuj tagi wg popularności
    tags_to_display.sort(key=lambda x: -x[2])

    # odetnij tagi których nie chcemy wyświetlać (popularność == 0 albo dalej niż 20. miejsce)
    tags_to_display = [x for x in tags_to_display if x[2] > 0]
    # poniższy kod jest zakomentowany,
    # ponieważ nie jest póki co potrzebny
    # if len(tags_to_display) > 20:
    #     tags_to_display = tags_to_display[0:20]

    context['tags_to_display'] = tags_to_display
    return render(request, 'sec/tags.html', context)


def join_or_leave(request, section_name, action):
    """ Funkcja obsługująca żądanie dołączenia do lub opuszczenia sekcji

    Note:
        W zależności od argumentu ``action`` wywołuje jedną z funkcji:
            - join
            - leave

    Args:
        request(WSGIRequest): obiekt klasy WSGIRequest
        section_name(str): nazwa sekcji, dla której chcemy pobrać posty
        action(str): akcja, patrz notka wyżej

    Returns:
        django.http.HtttpResponse: zwraca przekierowanie do adresu 'sec/sec.html'
        section_name(str): nazwa sekcji, do której użytkownik chce dołączyć lub którą chce opuścić
    """
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])
    current_user = context['current_user']
    if section_name != 'all':
        current_section = Section.objects.filter(name=section_name).first()
        if action == 'join':
            current_section.users.add(current_user)
        elif action == 'leave':
            current_section.users.remove(current_user)
    return redirect('sec:section', section_name)


def join(request, section_name):
    """ Funkcja obsługująca żądanie dołączenia do sekcji

    Args:
        request(WSGIRequest):obiekt klasy WSGIRequest
        section_name(str):nazwa sekcji, dla której chcemy pobrać posty

    Returns:
        django.http.HtttpResponse:obiekt reprezentujący wyrenderowany widok z funkcji join_or_leave po wybraniu akcji 'join'
        section_name(str):nazwa sekcji, dla której chcemy pobrać posty
    """
    return join_or_leave(request, section_name, 'join')


def leave(request, section_name):
    """ Funkcja obsługjąca żądanie opuszczenia sekcji

    Args:
        request(WSGIRequest):obiekt klasy WSGIRequest
        section_name(str):nazwa sekcji, dla której chcemy pobrać posty

    Returns:
        django.http.HtttpResponse:obiekt reprezentujący wyrenderowany widok z funkcji join_or_leave po wybraniu akcji 'leave'
        section_name(str):nazwa sekcji, dla której chcemy pobrać posty
    """
    return join_or_leave(request, section_name, 'leave')


def preferences(request, section_name='all'):
    """
    Funkcja, która renderuję podstronę preferences/

    Na tej stronie użytkownik może ustawić preferencje dla wybranych tagów.

    Args:
        request:WSGIRequest - obiekt klasy WSGIRequest
        section_name:str - nazwa sekcji dla której wyświetlamy punktacje tagów lub napis 'all' gdy chcemy wyswietlic wszystkie tagi w serwisie

    Returns:
        wyrenderowany kod html dla podstrony preferences.html

    Raises:
        Http404: gdy podano błędną nazwę sekcji lub użytkownik nie jest zalogowany
    """
    # Ustawia podstawowe atrybuty contextu i aktualizuje czas ostatniej aktywności użytkownika
    request.session['current_section_name'] = section_name
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])

    # Tworzy pomocnicze obiekty
    current_user = get_object_or_404(
        User, login=request.session.get('logged_in_as', default=None))
    tags_to_display = {}
    if section_name == 'all':
        for section in Section.objects.all():
            tags_to_display[section.description] = []
    else:
        current_section = get_object_or_404(Section, name=section_name)
        tags_to_display[current_section.description] = []

    # Pobiera odpowiednie rekordy z bazy TagPunctation
    tps = TagPunctation.objects.filter(user=current_user)
    for tp in tps:
        if tp.tag.section.description in tags_to_display.keys():
            tp.punctation = int(tp.punctation/10)
            tags_to_display[tp.tag.section.description].append(tp)
    context['tags_to_display'] = tags_to_display
    # Jeżeli użytkownik zezwala na zmianę swoich punktacji to zaznacz checkboxa na podstronie
    if current_user.is_punctation_changeable is True:
        context['is_punctation_changeable'] = 'checked'
    else:
        context['is_punctation_changeable'] = ''

    # Pobiera datę ostatniej aktualizacji preferencji użytkownika
    context['last_update_punctation_time'] = current_user.last_update_punctation_time

    # Renderuje podstronę
    return render(request, 'sec/preferences.html', context)


def update_punctation(request, section_name):
    """
    Funkcja, która zapisuje ustawione punktacje użytkownika w bazie danych w tabeli TagPunctation

    Args:
        request:WSGIRequest - obiekt klasy WSGIRequest, pola tego obiektu wykorzystywane w tej funkcji:
            -) .session['logged_is_as']:str - login zalogowanego użytkownika
        section_name:str - nazwa sekcji dla której modyfikujemy punktację tagów

    Returns:
        wyrenderowany kod html dla podstrony preferences.html

    Raises:
        Http404: gdy podano błędną nazwę sekcji lub użytkownik nie jest zalogowany
    """
    # Ustawia podstawowe atrybuty contextu i aktualizuje czas ostatniej aktywności użytkownika
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])

    # Tworzy obiekt typu User dla zalogowanego użytkownika
    current_user = get_object_or_404(
        User, login=request.session.get('logged_in_as', default=None))

    # Zapisuje punktacje w tabeli TagPunctation
    for tp in TagPunctation.objects.filter(user=context['current_user']):
        punctation = request.POST.get(str(tp.tag.id), default=None)
        if punctation is not None:
            tp.punctation = int(punctation)*10
            tp.save()

    # Zapisuje informację o tym czy użytkownik pozwala na modyfikację punktacji przez algorytm
    if request.POST.get('is_punctation_changeable', default=None) is None:
        current_user.is_punctation_changeable = False
    else:
        current_user.is_punctation_changeable = True

    # Aktualizuje czas ostatniej zmiany w preferencji
    current_user.update_last_update_punctation_time()

    # Zapisuje zmiany w bazie danych
    current_user.save()

    # Odsyła spowrotem do postrony preferences.html
    return redirect('sec:preferences', section_name)
