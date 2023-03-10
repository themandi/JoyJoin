import datetime
import json

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from common.context import set_common_context
from common.models import Post, Section, Tag, TagImplication, User
from common.activity import update_activity
from post.punctation import calculate_static_punctation


def create(request):
    """ Funkcja tworząca szablon tworzenia postu.

    Funkcja wstawia  dane takie jak 'Tutaj wpisz treść posta' aby stworzyc szablon dla użytkownika i przekierowuje na strone na której użytkownik może dodac post.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
        wyrenderowana strona create.html na której użytkownik może dodać swój post

    """

    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])

    preview_post = Post()
    preview_post.text = 'Tutaj wpisz treść posta'
    preview_post.title = 'Tytuł posta'
    preview_post.author = context['current_user']
    preview_post.creation_time = datetime.datetime.now()  # FIXME
    context['post'] = preview_post
    context['this_is_create_view'] = True

    return render(request, 'create/create.html', context)


def add(request):
    """ Funkcja dodająca post użytkownika do bazy.

    Funkcja dodaje  zapisane przez użytkownika dane takie jak tekst, tytuł, nazwe sekcji,tagi,login użytkownika.

    Sprawdza również wpisane tagi przez użytkownika i konwertuje je oraz usuwa te które się powtarzają.

    Wylicza także początkową punktację posta.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
        dodanie postu do bazy i przekierowanie na strone głowną

    Raises:
        Http404: gdy nie istnieje użytkownik

    Note:
        Pola wykorzystywane w obiekcie request:
        - .session.get['logged_in_as']: pobranie obiektu zalogowanego uzytkownika
        - .POST['post'] (str): treść posta wpisanego przez użytkownika
        - .POST['title'] (str): tytuł dodnay przez użytkownika
        - .POST['tags'] - tagi wpisane przez użytkownika
    """
    try:
        text = request.POST['post']
        title = request.POST['title']
        section_name = request.POST['section']
        tags = request.POST['tags']
    except (KeyError):
        return HttpResponse("Błąd POST")

    user_login = request.session.get('logged_in_as', default=None)
    if not user_login:
        return HttpResponse("Błąd sesji")
    user = get_object_or_404(User, login=user_login)

    destination_section = get_object_or_404(Section, name=section_name)
    if user not in destination_section.users.all():
        return HttpResponse("Błąd dodawania posta: nie należysz do sekcji " + destination_section.description)

    parsed_tags = tags.split(' ')
    approved_tags = set()
    user_tags = []
    for tag_name in parsed_tags:
        try:
            tag = Tag.objects.get(name=tag_name, section=destination_section)
            approved_tags.add(tag)
        except Tag.DoesNotExist:
            try:
                tag = Tag.objects.get(
                    slug=tag_name, section=destination_section)
                approved_tags.add(tag)
            except Tag.DoesNotExist:
                # konwertuje nazwę taga przez zastąpnienie podkreśleń myślnikami,
                # zastąpienie dużych liter małymi
                # i wyrzucenie nidozwolonych znaków (emoji i funkcjonalnego unikodu)
                # następnie wyrzuca potencjalny znak "-" z początku i końca
                # dodatkowo odrzuca tagi o nazwach dłuższych niż 31 znaków
                # (przykład: tojestprzykładtaguodługości32zna -- moim zdaniem zdecydowanie za długie na tag)
                new_tag_name = ''
                for char in tag_name:
                    if char.isalpha():
                        if char.isupper():
                            new_tag_name += char.lower()
                        else:
                            new_tag_name += char
                    elif char.isdecimal():
                        new_tag_name += char
                    elif char == '-':
                        new_tag_name += '-'
                    elif char == '_':
                        new_tag_name += '-'  # sic!

                first_alnum = 0
                for i in range(len(new_tag_name)):
                    if new_tag_name[i] != '-':
                        first_alnum = i
                        break
                last_alnum = len(new_tag_name) - 1
                for i in range(len(new_tag_name) - 1, -1, -1):
                    if new_tag_name[i] != '-':
                        last_alnum = i
                        break
                new_tag_name = new_tag_name[first_alnum:last_alnum + 1]

                if len(new_tag_name) <= 31:
                    user_tags.append(new_tag_name)

    # Szukamy tagów implikowanych przez te dodane przez użytkownika
    implied_tags = set()
    tags_to_process = set(approved_tags)
    while tags_to_process:
        tag = tags_to_process.pop()
        implied_set = TagImplication.objects.filter(
            parent__section=destination_section, parent=tag)
        for implied in implied_set:
            tags_to_process.add(implied.child)
            implied_tags.add(implied.child)

    # Usuwamy tagi implikowane z tagów dodanych wprost przez użytkownika
    # żeby uniknąć powtórek
    approved_tags -= implied_tags

    # Wylicza początkową punktację posta
    points = 0
    posts = Post.objects.filter(author=user)
    for post in posts:
        points = points + calculate_static_punctation(post, post.count_votes(1), post.count_votes(-1), post.count_all_comments(), False)
    if posts:
        points = points / len(posts)

    post = Post()
    post.author = user
    post.title = title
    post.text = json.loads(text)
    post.section = destination_section
    post.punctation = points
    if user_tags:
        post.user_tags = " ".join(user_tags)
    try:
        post.save()
    except ValidationError as error:
        return HttpResponse(error.message)  # FIXME czy to może tak zostać?
    for tag in approved_tags:
        post.tags.add(tag)
    for tag in implied_tags:
        post.implied_tags.add(tag)
    post.save()

    return redirect('all:all')
