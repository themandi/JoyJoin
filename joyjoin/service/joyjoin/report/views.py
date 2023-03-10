from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest

from common.context import set_common_context
from common.activity import update_activity
from report.models import Report, ReportCategory
from common.models import User


def report(request):
    """Funkcja renderująca strone report.html z podstawowymi danym na której możeym dodać opis zgłoszenia.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
        renderuje strone report.html z podstawowymi danymi
    """
    context = {}
    set_common_context(request, context)
    update_activity(context['current_user'])
    context['user_reports'] = Report.objects.filter(
        user=context['current_user']).order_by("-id")
    context['categories'] = ReportCategory.objects.all()

    # zgłoszenia do przeglądania dla admina
    # tutaj info czy zalogowany użytkownik jest adminem
    context['is_admin'] = False
    if context['is_admin']:
        context['all_reports'] = Report.objects.all().order_by("-id")

    return render(request, 'report/report.html', context)


def add(request):
    """Funkcja umożliwiająca dodanie zgłoszenia przez użytkownika.

    Args:
        request (WSGIRequest): obiekt klasy WSGIRequest

    Returns:
        przekierowuje na strone głowną po poprawnym zgłoszeniu

    Raises:
        Http404: gdy nie istnieje użytkownik.

    Note:
        Pola wykorzystywane w obiekcie request:
            - .POST['text'] (str) - treść zgłoszenia
            - .POST['category'] - kategoria zgłoszenia
    """
    try:
        text = request.POST['text']
        category = request.POST['category']
    except (KeyError):
        return HttpResponseBadRequest()

    if not text:
        return HttpResponseBadRequest()

    user_login = request.session.get('logged_in_as', default=None)
    user = None
    if user_login:
        user = get_object_or_404(User, login=user_login)

    report = Report()
    report.category = get_object_or_404(ReportCategory, name=category)
    report.text = text
    if user:
        report.user = user
    report.save()

    return redirect('all:all')
