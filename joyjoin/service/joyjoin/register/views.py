from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.dateparse import parse_date
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.utils import timezone

from common.context import set_common_context
from common.models import User
from common.activity import update_activity


def register(request):
    """ Jest to funkcja, która przedstawia stronę zawierającą formularz rejestracji dla użytkownika

    Args:
        request(WSGIRequest):obiekt klasy WSGIRequest

    Returns:
        django.http.HtttpResponse:obiekt reprezentujący wyrenderowany widok 'register/register.html' z ustawionym kontekstem szablonu
    """
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])
    context['is_register_site'] = True
    if context['current_user'] is not None:
        return redirect('all:all')
    else:
        return render(request, 'register/register.html', context)


def complete(request):
    """ Funkcja kompletująca rejestrację użytkownika.

    Args:
        request(WSGIRequest):obiekt klasy WSGIRequest

    Returns:
        django.http.HtttpResponse:zwraca przekierowanie do adresu 'register/register.html'
    """
    data = request.POST

    # Dokonaj sprawdzenia poprawności danych
    result = User.validate(data)

    if result[0] != 'OK':
        # Zwroc negatywna odpowiedz
        messages.add_message(request, messages.ERROR,
                             result[1], extra_tags=result[0])
    else:
        # Skonstruuj obiekt klasy 'User'
        user = User()
        user.name = data['name']
        user.login = data['login']
        user.email = data['email']
        user.password = make_password(data['password'])
        user.birth_date = parse_date(data['birth_date'])
        # TODO user powinien być oznaczony jako nieaktywny dopóki nie odbierze maila

        # Zapisz obiekt w bazie
        user.save()

        # Zwroc pozytywna odpowiedz
        messages.add_message(request, messages.SUCCESS,
                             result[1], extra_tags=result[0])
    return redirect('register:register')


def is_login_unused(request):
    try:
        login = request.POST["login"]
    except KeyError:
        return HttpResponse("false")

    if not login:
        return HttpResponse("false")

    if User.objects.filter(login=login).exists():
        return HttpResponse("false")
    else:
        return HttpResponse("true")


def is_password_uncommon(request):
    try:
        password = request.POST["password"]
    except KeyError:
        return HttpResponse("false")

    if not password:
        return HttpResponse("false")

    try:
        validate_password(password)
    except ValidationError as errors:
        for error in errors:
            if error.startswith('To hasło jest zbyt powszechne.'):
                return HttpResponse("false")
    return HttpResponse("true")


def is_age_ok(request):
    try:
        date_string = request.POST["date"]
    except KeyError:
        return HttpResponse("false")

    try:
        date = parse_date(date_string)
    except ValueError:
        return HttpResponse("false")
    if date is None:
        return HttpResponse("false")
    age = timezone.now().date() - date
    if not 12 * 365.25 <= age.days <= 120 * 365.25:
        return HttpResponse("false")
    return HttpResponse("true")
