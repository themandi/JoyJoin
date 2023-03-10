from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from common.context import set_common_context
from common.models import User
from common.activity import update_activity
from django.utils.datastructures import MultiValueDictKeyError
from PIL import Image
import os


def settings(request):
    """Funkcja renderująca strone ustawień z danymi zalogowanego użytkownika.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
         zwraca strone ustawień settings.html z wypełnionymi postawowowymi danymi.

    Raises:
        Http404: gdy nie istnieje użytkownik

    Note:
        Pola wykorzystywane w obiekcie request:
            - .session['logged_in_as'] (str) - nazwa zalogowanego użytkownika
            - .session.get('logged_in_as') - pobranie obiektu zalogowanego uzytkownika
    """
    if request.session.get('logged_in_as') is None:
        return redirect('login:login')
    username = request.session['logged_in_as']
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])
    user = get_object_or_404(User, login=username)
    context['user'] = user
    return render(request, 'settings/settings.html', context)


def complete(request):
    """Funkcja zmieniająca ustawienia podane przez użytkownika.

    Zajmuje się wgrywaniem awatara użytkownika z jednoczesna korekta rozmiaru oraz przypisuje zmienione przez użytkownika dane.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
        wywołuje funkcje settings która zwraca strone settings.html z poprawionymi danymi użytkownika oraz dodatkowo wyswietlany jest napis, że dane zostały poprawione

    Raises:
        wywołuje funkcje settings która zwraca strone settings.html oraz dodatkowo wyswietlany jest napis, jaki wystąpił błąd przy zapisywaniu nowych danych.
        Http404: gdy nie istnieje użytkownik.

    Note:
        Pola wykorzystywane w obiekcie request:
            - .FILES['image'] - obraz wgrany przez użytkownika
            - .session['logged_in_as'] (str) - nazwa zalogowanego użytkownika
    """
    if request.session.get('logged_in_as') is None:
        messages.add_message(request, messages.ERROR,
                             'Musisz być zalogowany!', extra_tags='not_logged')
        return redirect('login:login')

    username = request.session['logged_in_as']
    data = request.POST.copy()
    data['login'] = username
    # Dokonaj sprawdzenia poprawności danych
    result = User.validate(data, source='settings')
    if result[0] != 'OK':
        # Zwroc negatywna odpowiedz
        messages.add_message(request, messages.ERROR,
                             result[1], extra_tags=result[0])
        return redirect('settings:settings')
    else:
        user = get_object_or_404(User, login=username)
        user.name = data['name']
        user.email = data['email']
        if data['password'] != '' and data['password_2'] != '':
            user.password = make_password(data['password'])
        user.birth_date = parse_date(data['birth_date'])
        user.description = data['description']
        user.save()
        try:
            if request.method == 'POST' and request.FILES['image']:
                upl_image = request.FILES['image']
                last_picture = user.image
                last_picture_mini = user.image_mini
                user.image = upl_image
                user.image_mini = upl_image
                if user.width_field is None:
                    messages.add_message(request, messages.ERROR,
                                         'Wybrano zły typ pliku', extra_tags='Zle')
                    return redirect('settings:settings')

                else:

                    user.save()
                    img = Image.open(user.image.path)
                    img_mini = Image.open(user.image_mini.path)
                    extension = os.path.splitext(user.image.path)

                    if img.width > img.height:
                        img = img.crop(
                            ((img.width - img.height)/2, 0, (img.width + img.height)/2, img.height))
                        img_mini = img.copy()
                        size = (400, 400)
                        size_mini = (80, 80)
                        img.thumbnail(size)
                        img_mini.thumbnail(size_mini)
                        img.save(user.image.path)
                        img_mini.save(user.image_mini.path)

                    elif img.height > img.width:
                        img = img.crop(
                            (0, (img.height - img.width)/2, img.width, (img.height + img.width)/2))
                        img_mini = img.copy()
                        size = (400, 400)
                        size_mini = (80, 80)
                        img.thumbnail(size)
                        img_mini.thumbnail(size_mini)
                        img.save(user.image.path)
                        img_mini.save(user.image_mini.path)

                    elif img.height == img.width:
                        img_mini = img.copy()
                        size = (400, 400)
                        size_mini = (80, 80)
                        img.thumbnail(size)
                        img_mini.thumbnail(size_mini)
                        img.save(user.image.path)
                        img_mini.save(user.image_mini.path)

                    copy_crop = user.image
                    copy_crop_mini = user.image_mini

                    if last_picture != 'default.jpg' and last_picture_mini != 'default_mini.jpg':
                        user.image = last_picture
                        user.image_mini = last_picture_mini
                        user.image.delete()
                        user.image_mini.delete()

                    user.image = copy_crop
                    user.image_mini = copy_crop_mini
                    path_image = user.image.path
                    path_mini_image = user.image_mini.path
                    path_dir_image = os.path.dirname(user.image.path)
                    new_path = path_dir_image + '/' + user.login + extension[1]
                    os.rename(path_image, new_path)
                    new_path = path_dir_image + '/' + \
                        user.login + '_mini' + extension[1]
                    os.rename(path_mini_image, new_path)
                    user.image = user.login + extension[1]
                    user.image_mini = user.login + '_mini' + extension[1]
                    user.save()

        except MultiValueDictKeyError:
            pass

        # Zwróć odpowiedź
        messages.add_message(request, messages.SUCCESS,
                             'Dane użytkownika zostały poprawione', extra_tags='OK')
        return redirect('settings:settings')
