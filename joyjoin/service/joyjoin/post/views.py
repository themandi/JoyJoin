from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404

from common.context import set_common_context
from common.activity import update_activity
from common.models import Post, Vote, User, Comment, CommentVote
from common.models import comment_max_depth
from common.comment_sorting import comment_sorting_keys, sort_comments

from common.queries import get_comments_list, get_posts


def post(request, post_id):
    """ Funkcja wyświetląca posta o podanym id

    Funkcja wyświetlająca treść posta, jego oceny oraz komentarze znajdujące się pod nim (i oceny komentarzy).

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest
        post_id (int): id posta do wyświetlenia

    Returns:
        wyrenderowany kod HTML z postem

    Note:
        Pola wykorzystywane w obiekcie request:
            - .session['logged_in_as'] (str): nazwa zalogowanego użytkownika
            - .session['sort_type'] (str): typ sortowania komentarzy
    """
    try:
        post = Post.objects.get(id=post_id)
    except (Post.DoesNotExist):
        raise Http404()

    is_liked = False
    is_disliked = False
    try:
        user = User.objects.get(login=request.session['logged_in_as'])
        update_activity(user)
        if Vote.objects.filter(post=post, user=user.id, reaction=1).exists():
            is_liked = True
        if Vote.objects.filter(post=post, user=user.id, reaction=-1).exists():
            is_disliked = True
    except (KeyError, User.DoesNotExist):
        pass
    finally:
        liked = post.count_votes(reaction=1)
        disliked = post.count_votes(reaction=-1)
        context = {
            'post': post,
            'liked': liked,
            'disliked': disliked,
            'is_liked': is_liked,
            'is_disliked': is_disliked,
        }
        set_common_context(request, context)
    context['this_is_the_all_view'] = True
    context['comment_max_depth'] = comment_max_depth

    sort_types = []
    for sort_type in comment_sorting_keys:
        sort_types.append(sort_type)
    context['sort_types'] = sort_types

    selected_sort_type = request.session.get('sort_type', default='najnowsze')
    context['selected_sort_type'] = selected_sort_type

    comments = post.get_top_level_comments()
    comments_list = []
    for comm in sort_comments(comments, selected_sort_type):
        comments_list += get_comments_list(comm,
                                           selected_sort_type, context['current_user'])

    context['comments_list'] = comments_list
    context['this_is_post_view'] = True

    context['this_is_post_view'] = True

    return render(request, 'post/post.html', context)


def vote_comment(request, option):
    """ Funkcja dodająca ocenę pod komentarzem

    Funkcja dodaje lub usuwa ocenę pod komentarzem. Ocena zapisywana jest w bazie danych.
    Jeżeli użytkownik nie jest zalogowany, to ocena nie zostanie dodana/usunięta i wyrenderowana zostanie pusta strona.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest
        option (int): wybrany rodzaj oceny, możliwe opcje:

            - 1, dodanie lajka lub usunięcie go, jeżeli lajk był dany już wcześniej
            - 2, dodanie dislajka lub usunięcie go, jeżeli dislajk był dany już wcześniej

    Returns:
        wyrenderowany kod HTML z odpowiednią oceną uzytkownika lub common/empty.html jeżeli użytkownik nie jest zalogowany

    Note:
        Pola wykorzystywane w obiekcie request:
            - .session['logged_in_as'] (str): nazwa zalogowanego użytkownika
            - .POST['comm_id'] (str): id komentarza do ocenienia
    """
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])

    try:
        user = User.objects.get(
            login=request.session.get('logged_in_as', default=None))
    except (KeyError, User.DoesNotExist):
        return render(request, "common/empty.html", context)

    comment = get_object_or_404(Comment, id=request.POST.get('comm_id'))

    if option == 1:
        reaction = 1
    elif option == 2:
        reaction = -1
    else:
        return render(request, "common/empty.html", context)

    if CommentVote.objects.filter(user=user, comment=comment).exists():
        vote = CommentVote.objects.filter(user=user, comment=comment).first()
        if vote.get_reaction() == reaction:
            vote.delete()
        else:
            vote.reaction = reaction
            vote.save()
    else:
        vote = CommentVote(user=user, comment=comment, reaction=reaction)
        vote.save()

    is_liked = False
    is_disliked = False
    if CommentVote.objects.filter(comment=comment, user=user.id, reaction=1).exists():
        is_liked = True
    if CommentVote.objects.filter(comment=comment, user=user.id, reaction=-1).exists():
        is_disliked = True
    liked = comment.count_votes(reaction=1)
    disliked = comment.count_votes(reaction=-1)
    context = {
        'liked': liked,
        'disliked': disliked,
        'is_liked': is_liked,
        'is_disliked': is_disliked,
    }

    return render(request, 'post/likes.html', context)


def change_sorting(request):
    """ Funkcja zmieniająca rodzaj sortowania komentarzy

    Funkcja zmienia rodzaj sortowania komentarzy na wybrany przez użytkownika.
    Rodzaje sortowania są wybierane z common.comment_sorting.py (domyślnie najnowsze)

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
        wyrenderowany kod HTML posta z nowym rodzajem sortowania komentarzy

    Note:
        Pola wykorzystywane w obiekcie request:
            - .POST['post_id'] (str): id aktualnie przeglądanego posta
            - .POST['sort_type'] (str): wybrany przez użytkownika (z listy) typ sortowania
            - .session['sort_type'] (str): wybrany przez użytkownika typ sortowania (zapisany w request.session)
    """
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])

    post_id = request.POST.get('post_id', default=None)
    if not post_id:
        raise Http404()

    request.session['sort_type'] = request.POST.get(
        'sort_type', default='najnowsze')

    return redirect('post:post', post_id)


def reply(request):
    """ Funkcja dodająca komentarz pod postem lub innym komentarzem

    Funkcja dodaje komntarz pod wybranym przez użytkownika elementem (post lub komentarz).
    Nowy komentarz zapisywany jest w bazie danych, jeżeli formularz posiada prawidłowe dane.
    Jeżeli użytkownik nie jest zalogowany, to komentarz nie zostanie dodany i wyrenderowana zostanie pusta strona.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
        wyrenderowany kod HTML widoku przeglądanego posta z nowym komentarzem (o ile został dodany) lub common/empty.html jeżeli użytkownik nie jest zalogowany

    Note:
        Pola wykorzystywane w obiekcie request:
            - .session['logged_in_as'] (str): nazwa zalogowane użytkownika
            - .POST['post_id'] (str): id posta bezpośrednio pod którym ma być dodany nowy komentarz lub "None", jeżeli ma być dodany pod innym komentarzem
            - .POST['comm_id'] (str): id komentarza pod którym ma być dodany nowy komentarz lub "None", jeżeli ma być dodany bezpośrednio pod postem
            - .POST['comment'] (str): treść komentarza
    """
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])

    parent_post = get_object_or_404(Post, id=request.POST.get('post_id'))

    text = request.POST.get("comment")
    if not text:
        raise Http404()

    try:
        author = User.objects.get(
            login=request.session.get('logged_in_as', default=None))
    except (KeyError, User.DoesNotExist):
        return render(request, "common/empty.html", context)

    comm = Comment(text=text, author=author, parent_post=parent_post)

    if not request.POST.get('comm_id'):
        raise Http404()

    if request.POST.get('comm_id') != 'None':
        comm.parent_comment = get_object_or_404(
            Comment, id=request.POST.get('comm_id'))
        if comm.get_depth() <= comment_max_depth:
            comm.save()
    else:
        comm.save()

    return redirect('post:post', parent_post.id)


def vote(request, option):
    """ Funkcja dodająca ocenę pod postem

    Funkcja dodaje lub usuwa ocenę pod postem. Ocena zapisywana jest w bazie danych.
    Jeżeli użytkownik nie jest zalogowany, to ocena nie zostanie dodana/usunięta i wyrenderowana zostanie pusta strona.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest
        option (int): wybrany rodzaj oceny, możliwe opcje:

            - 1, dodanie lajka lub usunięcie go, jeżeli lajk był dany już wcześniej
            - 2, dodanie dislajka lub usunięcie go, jeżeli lajk był dany już wcześniej

    Returns:
        wyrenderowany kod HTML z odpowiednią oceną uzytkownika lub common/empty.html jeżeli użytkownik nie jest zalogowany

    Note:
        Pola wykorzystywane w obiekcie request:
            - .session['logged_in_as'] (str): nazwa zalogowanego użytkownika
            - .POST['post_id'] (str): id posta do ocenienia
    """
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])

    v = Vote()
    post = get_object_or_404(Post, id=request.POST.get('post_id'))

    try:
        user = User.objects.get(
            login=request.session.get('logged_in_as', default=None))
    except (KeyError, User.DoesNotExist):
        return render(request, "common/empty.html", context)

    if Vote.objects.filter(post=post, user=user.id).exists():
        v = Vote.objects.get(post=post, user=user)

        if Vote.objects.filter(post=post, user=user.id, reaction=1).exists():
            if option == 1:
                v.delete()
            elif option == 2:
                v.reaction = -1
                v.save()
        elif Vote.objects.filter(post=post, user=user.id, reaction=-1).exists():
            if option == 1:
                v.reaction = 1
                v.save()
            elif option == 2:
                v.delete()
    else:
        v.post = post
        v.user = user
        if option == 1:
            v.reaction = 1
        elif option == 2:
            v.reaction = -1
        v.save()

    is_liked = False
    is_disliked = False
    if Vote.objects.filter(post=post, user=user.id, reaction=1).exists():
        is_liked = True
    if Vote.objects.filter(post=post, user=user.id, reaction=-1).exists():
        is_disliked = True
    liked = post.count_votes(reaction=1)
    disliked = post.count_votes(reaction=-1)
    context = {
        'liked': liked,
        'disliked': disliked,
        'is_liked': is_liked,
        'is_disliked': is_disliked,
    }

    return render(request, 'post/likes.html', context)


def display_new_posts(request):
    """ Funkcja, która pobiera nowe posty i renderuje kod html zawierający te posty.

    Przyjmuje ona parametry znajdujące się w request.POST i zwraca kod HTML nowych postów,
    które chcemy wyświetlić użytkownikowi przy scrollowaniu strony.
    Wywoływana poprzez Ajax w kodzie JavaScript.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
        wyrenderowany kod HTML z nowymi postami

    Note:
        Pola wykorzystywane w obiekcie request:
            - .session['logged_in_as'] (str): nazwa zalogowane użytkownika
            - .session['list_of_displayed_posts'] (list(int)): lista indeksów wyświetlonych postów przez uzytkownika w danej sesji
            - .POST['section_name'] (str): nazwa sekcji, dla której chcemy wyświetlić posty
            - .POST['tag_name'] (str): nazwa tagu, dla którego chcemy wyświetlić posty
            - .POST['user_name'] (str): nazwa użytkownika, dla którego chcemy wyświetlić posty
            - .POST['number_of_posts'] (str): ilość postów które chcemy wyświetlić,
              jeżeli ten napis nie będzie reprezentował liczby to zostanie wyrenderowana zerowa ilość postów
    """
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])
    context['this_is_the_all_view'] = True
    section_name = request.POST.get('section_name', default=None)
    tag_name = request.POST.get('tag_name', default=None)
    user_name = request.POST.get('user_name', default=None)
    number_of_posts = request.POST.get('number_of_posts', default=None)

    if number_of_posts is not None:
        try:
            number_of_posts = int(request.POST.get('number_of_posts'))
        except (Exception):
            number_of_posts = 0
    else:
        number_of_posts = 5

    context['posts_to_display'] = get_posts(
        request, section_name, tag_name, user_name, number_of_posts)

    return render(request, "post/new_posts.html", context)
