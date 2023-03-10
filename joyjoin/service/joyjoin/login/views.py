from django.contrib.auth.hashers import check_password
from django.http import HttpResponse
from django.shortcuts import redirect, render

from common.context import set_common_context
from common.models import User
from common.activity import update_activity


def login(request):
    """Funkcja renderująca strone przy podaniu błednych danych.

    Strona jest renderowana jeśli użytkownik podał zły login albo hasło.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
        renderuje strone login.html na której jest opis jaki wystąpił podczas logowania
    """
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])
    if context['current_user'] is not None:
        return redirect('all:all')
    else:
        return render(request, 'login/login.html', context)


def verify(request):
    """Funkcja weryfikująca potrzebne dane do logowania przez użytkownika.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
        przekierowanie na główną strone jeżeli użytwkonik podał prawidłowe dane

    Raises:
        gdy podany bedzie login nie znajdujący się w bazie lub hasło jest nie poprawne do podanego loginu zostanie wywołana funkcja login(renderuje strone login.html)

    Note:
        Pola wykorzystywane w obiekcie request:
            - .POST['login'] (str): login użytkownika
            - .POST['password'] (str): hasło użytkownika
    """
    try:
        given_login_or_email = request.POST['login']
        password = request.POST['password']
        # remember = request.POST['remember']
    except (KeyError):
        return HttpResponse("Wystąpił błąd podczas logowania: błąd POST")
    try:
        user = None
        try:
            user = User.objects.get(login=given_login_or_email)
        except(User.DoesNotExist):
            user = User.objects.get(email=given_login_or_email)
    except (User.DoesNotExist):
        return redirect('login:login')

    if check_password(password, user.password):
        request.session['logged_in_as'] = user.login
        return redirect('all:all')

    return redirect('login:login')


def logout(request):
    """Funkcja wylogowująca użytkownika.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
        przekierowanie na główną strone przy poprawnym wylogowaniu

    Note:
        Pola wykorzystywane w obiekcie request:
            - .session['logged_in_as'] - do zmiany zalogowanego uzytkownika
    """
    request.session['logged_in_as'] = None
    return redirect('all:all')
