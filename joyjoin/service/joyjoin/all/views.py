from sec.views import section, render
from common.context import set_common_context


def all(request):
    """ Jest to funkcja, która przedstawia główną stronę.

    Strona ta zawiera posty, komentarze, liste sekcji oraz inne dostępne opcje.

    Args:
        request(WSGIRequest):obiekt klasy WSGIRequest

    Returns:
        django.http.HtttpResponse:obiekt reprezentujący wyrenderowany widok 'all'
    """
    return section(request, 'all')


def about(request):
    context = {}
    set_common_context(request, context)

    if request.session.get('logged_in_as') is None:
        return render(request, 'all/about.html', context)
    return all(request)


def error_404(request, exception=None):
    """ Jest to funkcja, która przedstawia stronę podczas błędu 404.

    Strona ta zawiera własny design oraz odnośniki do strony głównej i zgłoszenia błędu.

    Args:
        request(WSGIRequest):obiekt klasy WSGIRequest
        exception(bool):None,nie uwzględniamy wyjątków

    Returns:
        django.http.HtttpResponse:obiekt reprezentujący wyrenderowany widok 'all/error_404.html'
        gdy nasza strona będzie zwracała status równy 404
    """
    return render(request, 'all/error_404.html', status=404)


def regulamin(request):
    """ Jest to funkcja, która przedstawia strone zawierającą regulamin strony

    Args:
        request(WSGIRequest):obiekt klasy WSGIRequest

    Returns:
        django.http.HtttpResponse:obiekt reprezentujący wyrenderowany widok 'all/regulamin.html' z ustawionym kontekstem szablonu
    """
    context = {}
    set_common_context(request, context)
    return render(request, 'all/regulamin.html', context)
