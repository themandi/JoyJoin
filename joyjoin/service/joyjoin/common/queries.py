""" Moduł dostarczania list oraz szczegółowych informacji postów, komentarzy

    Moduł zawiera funkcje pomocnicze służące do pobierania list postów i
    komentarzy (speniających konkretne wymagania)
    oraz do pobierania szczegółowych informacji o postach i komentarzach.

"""
from django.shortcuts import get_object_or_404
from itertools import chain

from common.comment_sorting import sort_comments
from common.models import Post, Section, Tag, Vote, User, CommentVote, max_comments_in_sec_view
from common.updates import update_post_visits, update_tag_punctations
from post.punctation import calculate_punctation


def get_comments_list(comment, sort_type, user):
    """ Rekurencyjna funkcja tworząca listę komentarzy spod podanego komentarza.

    Rekurencyjna funkcja tworząca listę wszystkich komentarzy znajdujących się pod podanym w argumencie komentarzu.

    Funkcja ta wpisuje na listę komentarze przechodząc przez ich strukturę metodą DFS,
    o krawędziach komentarz_nadrzędny -> komentarz_pochodny (odpowiedź), a
    wierzchołkiem startowym jest komentarz podany w argumencie funkcji.

    Lista zawiera odpowiednie informacje o każdym zawartym w niej komentarzu. Komentarze sortowane są według wybranej metody.

    Args:
        comment (common.models.Comment): komentarz (parent), na którego odpowiedzi będą zapisywane na listę
        sort_type (str): typ sortowania komentarzy (wybierane spośród typów z common.comment_sorting)
        user (common.models.User): zalogowany uzytkownik lub None (dla niezalogowanych użytkowników)

    Returns:
        list(tuple): lista krotek zawierających, kolejno:

            - comment (common.models.Comment): komentarz
            - comm_likes (int): liczba lajków komentarza
            - comm_dislikes (int): liczba dislajków komentarza
            - comm_is_liked (bool): informacja, czy komentarz dostał lajka (lub False, jeżeli użytkownik niezalogowany)
            - comm_is_disliked (bool): informacja, czy komentarz dostał dislajka (lub False, jeżeli użytkownik niezalogowany)

            po wypisaniu wszystkich odpowiedzi pod komentarzem w liście znajduje się specjalna krotka (')', '', '', '', '') o tym informująca
    """
    list = []

    comm_is_liked = False
    comm_is_disliked = False
    if CommentVote.objects.filter(comment=comment, user=user, reaction=1).exists():
        comm_is_liked = True
    if CommentVote.objects.filter(comment=comment, user=user, reaction=-1).exists():
        comm_is_disliked = True

    comm_likes = comment.count_votes(1)
    comm_dislikes = comment.count_votes(-1)

    list.append((comment, comm_likes, comm_dislikes,
                 comm_is_liked, comm_is_disliked))
    if comment.get_direct_replies().exists():
        for comm in sort_comments(comment.get_direct_replies(), sort_type):
            list += get_comments_list(comm, sort_type, user)

    list.append((')', '', '', '', ''))
    return list


def get_simple_comments_list(post, user):
    """ Funkcja tworząca listę (pewnych) komentarzy bezpośrednio pod postem.

    Funkcja tworząca listę (pewnych) komentarzy znajdujących się bezpośrednio pod podanym w argumencie postem.

    Lista zawiera odpowiednie informacje o każdym wyświetlonym komentarzu pod postem.
    Na listę wypiywane są jedynie niektóre komentarze, znajdujące się bezpośrednio pod postem
    - dostarczane są przez funkcję post.get_top_level_comments().

    Args:
        post (common.models.Post): post, którego komentarze będą zapisywane na listę
        user (common.models.User): zalogowany uzytkownik lub None (dla niezalogowanych użytkowników)

    Returns:
        list(tuple): lista krotek zawierających, kolejno:

            - comment (common.models.Comment): komentarz
            - comm_likes (int): liczba lajków komentarza
            - comm_dislikes (int): liczba dislajków komentarza
            - comm_is_liked (bool): informacja, czy komentarz dostał lajka (lub False, jeżeli użytkownik niezalogowany)
            - comm_is_disliked (bool): informacja, czy komentarz dostał dislajka (lub False, jeżeli użytkownik niezalogowany)
    """
    comments_to_display = []
    for comment in post.get_top_level_comments(max_comments_in_sec_view):
        comm_is_liked = False
        comm_is_disliked = False
        if CommentVote.objects.filter(comment=comment, user=user, reaction=1).exists():
            comm_is_liked = True
        if CommentVote.objects.filter(comment=comment, user=user, reaction=-1).exists():
            comm_is_disliked = True

        comm_likes = comment.count_votes(1)
        comm_dislikes = comment.count_votes(-1)

        comments_to_display.append(
            (comment, comm_likes, comm_dislikes, comm_is_liked, comm_is_disliked))
    return comments_to_display


def get_extra_information_for_post(post, current_user=None):
    """ Funkcja dołączająca dodatkowe informacje do posta.

    Dla każdego postu pobiera ilość lajków, ilość dislajków, informację czy użytkownik polajkował post, informację czy użytkownik zdislajkował post oraz listę komentarzy które chcemy wyświetlić

    Args:
        post (common.models.Post): post, dla którego chcemy pobrać dodatkowe informacje
        current_user (common.models.User): obecnie zalogowany użytkownik. Wymagany do pobrania informacji o tym, czy zalogowany użytkownik polajkował/zdislajkował ten post lub wyświetlane komentarze pod tym postem.

    Returns:
        (tuple): krotkę zawierającą, kolejno:

            - post (common.models.Post): post
            - likes (int): ilość lajków pod postem
            - dislikes (int): ilość dislajków pod postem
            - is_liked (bool): informacja czy użytkownik polajkował post
            - is_disliked (bool): informacja czy użytkownik zdislajkował post
            - comments ([common.models.Post]): lista komentarzy
    """
    is_liked = False
    is_disliked = False
    if Vote.objects.filter(post=post, user=current_user, reaction=1).exists():
        is_liked = True
    if Vote.objects.filter(post=post, user=current_user, reaction=-1).exists():
        is_disliked = True

    comments = get_simple_comments_list(post, current_user)
    return (post, post.count_votes(1), post.count_votes(-1), is_liked, is_disliked, comments)


def get_posts_for_user(user_name):
    """ Funkcja, zwracająca listę postów utworzonych przez konkretnego użytkownika.

    Args:
        user_name (str): nazwa użytkownika, dla którego chcemy pobrać posty

    Returns:
        list(common.models.Post): lista postów zgodnych z podanymi parametrami

    Raises:
        Http404: gdy podano nieistniejącą nazwę użytkownika
    """
    user = get_object_or_404(User, login=user_name)
    return Post.objects.filter(author=user).order_by('-creation_time')


def get_posts_for_section(section_name):
    """ Funkcja, zwracająca listę postów znajdujących sie w podanej sekcji.

    Args:
        section_name (str): nazwa sekcji, dla której chcemy pobrać posty

    Returns:
        list(common.models.Post): lista postów zgodnych z podanymi parametrami

    Raises:
        Http404: gdy podano nieistniejącą nazwę sekcji
    """
    if section_name != 'all':
        current_section = get_object_or_404(Section, name=section_name)
        posts_to_display = Post.objects.filter(
            section=current_section).order_by('-creation_time')
    else:
        posts_to_display = Post.objects.order_by('-creation_time')

    return posts_to_display


def get_posts_with_tag(section_name, tag_name):
    """ Funkcja, zwracająca listę postów z konkretnym tagiem.

    Args:
        section_name (str): nazwa sekcji, dla której chcemy pobrać posty
        tag_name (str): nazwa tagu, dla którego chcemy pobrać posty

    Returns:
        list(common.models.Post): lista postów zgodnych z podanymi parametrami

    Raises:
        Http404, gdy podano nieistniejącą nazwę sekcji
    """
    current_section = get_object_or_404(Section, name=section_name)

    try:
        tag = Tag.objects.get(section=current_section, name=tag_name)
        posts_to_display = list(chain(
            Post.objects.filter(section=current_section, tags=tag),
            Post.objects.filter(
                section=current_section, implied_tags=tag),
        ))
    except Tag.DoesNotExist:
        try:
            tag = Tag.objects.get(
                section=current_section, slug=tag_name)
            posts_to_display = list(chain(
                Post.objects.filter(section=current_section, tags=tag),
                Post.objects.filter(
                    section=current_section, implied_tags=tag),
            ))
        except Tag.DoesNotExist:
            candidate_posts = Post.objects.filter(
                section=current_section)
            posts_to_display = []
            for post in candidate_posts:
                if tag_name in post.user_tags_as_list():
                    posts_to_display.append(post)

    return posts_to_display


def get_posts(request, section_name=None, tag_name=None, user_name=None, number_of_posts=3):
    """ Funkcja, pobierająca posty z bazy danych, według zadanych kryteriów.

    Funkcja w zależności od podanych argumentów wywołuje funkcje pomocnicze:
        - get_posts_for_user() - gdy jest podany argument user_name
        - get_posts_with_tag() - gdy jest podany argument tag_name oraz section_name
        - get_posts_for_section() - gdy jest podany argument section_name

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest
        section_name (str): nazwa sekcji, dla której chcemy pobrać posty
        tag_name (str): nazwa tagu, dla którego chcemy pobrać posty
        user_name (str): nazwa użytkownika, dla którego chcemy pobrać posty
        number_of_posts (int): liczba postów jakie chcemy pobrać

    Returns:
        list(tuple): lista krotek z postów (i dodatkowych parametrów) zgodnych z podanymi parametrami (w szczególności może to być pusta lista, gdy użytkownik pobrał już wszystkie posty)

    Raises:
        Http404: gdy podano nieistniejącą nazwę sekcji lub użytkownika

    Note:
        Pola wykorzystywane w obiekcie request:
            - .session['logged_in_as'] (str): nazwa zalogowanego użytkownika
            - .session['list_of_displayed_posts'] ([int]): lista indeksów wyświetlonych postów przez uzytkownika w danej sesji

    Note:
        Funkcja zwraca krotkę zawierającą elementy:
            - post (common.models.Post): post
            - likes (int): ilość lajków pod postem
            - dislikes (int): ilość dislajków pod postem
            - is_liked (bool): informacja czy użytkownik polajkował post
            - is_disliked (bool): informacja czy użytkownik zdislajkował post
            - comments ([common.models.Post]): lista komentarzy
    """
    # Pobiera z sesji listę wyświetlonych postów
    list_of_displayed_posts = request.session.get(
        'list_of_displayed_posts', default=[])
    if len(list_of_displayed_posts) == 0:
        request.session['list_of_displayed_posts'] = []

    # Jezeli liczba postow jakie chcemy pobrac jest niedodatnia to zwracamy pustą listę
    if number_of_posts <= 0:
        return []

    # Pobiera posty z bazy danych
    if user_name is not None:
        selected_posts = get_posts_for_user(user_name)
    elif tag_name is not None:
        selected_posts = get_posts_with_tag(section_name, tag_name)
        if selected_posts is None:
            return None
    else:
        selected_posts = get_posts_for_section(section_name)

    # Tworzy obiekt klasy User
    try:
        current_user = User.objects.get(
            login=request.session.get('logged_in_as', default=''))
    except (User.DoesNotExist):
        current_user = None

    # Do postow dodaje informacje o likach i dislikach
    posts_to_display = []
    for post in selected_posts:
        if post.id not in list_of_displayed_posts:
            posts_to_display.append(
                get_extra_information_for_post(post, current_user))

    # Akualizuje tabelę TagPunctation (jezeli spelnione zostaną odpowiednie warunki)
    if current_user is not None:
        update_tag_punctations(current_user)

    # Dla kazdego posta wylicza punktację i sortuje malejąco względem tej punktacji (posty na podstronie uzytkownika sa sortowane według daty publikacji)
    if user_name is None:
        posts_to_display.sort(key=lambda x: calculate_punctation(
            x[0], x[1], x[2], x[0].count_all_comments(), current_user), reverse=True)

    # Ogranicza ilość zwracanych postów
    posts_to_display = posts_to_display[0:number_of_posts]

    # Aktualizuje tabelę PostVisit
    if current_user is not None:
        update_post_visits(posts_to_display, current_user)

    # Dodaje posty które za chwilę wyświetli użytkownik do listy wyświetlonych postów
    for post in posts_to_display:
        request.session['list_of_displayed_posts'].append(post[0].id)
    request.session.save()

    # Zwraca liste postow zgodne z kryteriami
    return posts_to_display
