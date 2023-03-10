""" Moduł obliczający punktację

Moduł zawiera informacje o poziomach istotności poszczególnych czynników np.
ocen, komentarzy, liczby odwiedzin.
Posiada funkcje za pomocą których możliwe jest wyliczenie punktacji posta lub
tagu na podstawie informacji z
bazy danych i ustalonych poziomach istotności poszczególnych czynników.

"""
import datetime

from math import copysign

from common.models import TagPunctation, PostVisit

# Uwaga: suma współczynników w każdym słowniku powinna wynosić 1
# Współczynniki istotności punktacji statycznej i specyficznej
a = {'static': 0.2,
     'specific': 0.8}

# Współczynniki istotności w punktacji statycznej
b = {'initial': 0.1,
     'votes': 0.3,
     'comments': 0.2,
     'time': 0.5}

# Współczynniki istotności w punktacji specyficznej
c = {'tags': 0.4,
     'visits': 0.5,
     'belongs': 0.1}

# Współczynniki istotności w punktacji specyficznej tagów
d = {'initial': 0.6,
     'votes': 0.2,
     'comments': 0.2}

# Współczynniki istotności w ocenach posta/tagu
e = {'likes': 0.6,
     'dislikes': 0.4}

# Współczynniki wzrostu (Dla jakiej wielkości danego czynniku, post ma uzyskać 50% możliwych punktów za określony czynnik)
w = {'post_votes': 1,
     'post_comments': 1,
     'post_time': 24,
     'post_visits': 1,
     'tag_votes': 2,
     'tag_comments': 2}


def sgn(x):
    return copysign(1, x)


def f(likes, dislikes):
    ''' Funkcja pomocnicza.

    Oblicza różnicę ważoną między ilością lajków a ilością dislajków pewnego posta/tagu (w założeniu lajki mają większą istotność niż dislajki)

    Args:
        likes (int): ilość lajków pod pewnym postem/tagiem
        dislikes (int): ilość dislajków pod pewnym postem/tagiem

    Returns:
        float: liczba reprezentująca różnicę ważoną lajków i dislajków
    '''
    return e['likes']*likes - e['dislikes']*dislikes


def F(x, w):
    ''' Funkcja pomocnicza.

    Oblicza punktację pewnego czynnika w zależności od wielkości czynnika i współczynnika wzrostu.

    Args:
        x (float): wielkość pewnego czynnika
        w (float): współczynnik wzrostu czynnika (Dla jakiej wielkości argumentu x, funkcja ma zwrócić wartość 50)

    Info:
        Szczegółowe informacje o funkcji F można znaleźć w opisie algorytmu

    Returns:
        float: liczba z zakresu (-100, 100), która reprezentuje wyliczoną punktację za określony czynnik
    '''
    return sgn(x) * (1 - 0.5**(abs(x)/w)) * 100


def calculate_punctation(post, likes, dislikes, comments, user=None):
    ''' Funkcja, która oblicza końcową punktację dla posta.

    Args:
        post (common.models.Post): post dla którego liczymy punktację
        likes (int): ilość lajków pod postem
        dislikes (int): ilość dislajków pod postem
        comments (int): ilość komentarzy pod postem
        user (common.models.User): zalogowany użytkownik, ja którego obliczamy punktację

    Returns:
        float: liczba z zakresu (-100, 100) reprezentująca końcową punktację dla posta
    '''
    if user:
        return a['static']*calculate_static_punctation(post, likes, dislikes, comments) + a['specific']*calculate_specific_punctation(post, user)
    else:
        return calculate_static_punctation(post, likes, dislikes, comments)


def calculate_static_punctation(post, likes, dislikes, comments, count_time=True):
    ''' Funkcja, która oblicza statyczną punktację dla posta.

    Args:
        post (common.models.Post): post dla którego liczymy punktację
        likes (int): ilość lajków pod postem
        dislikes (int): ilość dislajków pod postem
        comments (int): ilość komentarzy pod postem
        count_time (bool): True, gdy chcemy uwzględnić czas publikacji posta, False wpw. (czasu nieuwzględniamy przy obliczaniu początkowej punktacji posta)

    Returns:
        flaot: liczba z zakresu (-100, 100) reprezentująca statyczną punktację dla posta
    '''
    # Oblicza ile godzin minęło od publikacji postu
    if count_time:
        creation_time = post.creation_time
        time_difference = datetime.datetime.now() - datetime.datetime(creation_time.year, creation_time.month,
                                                                      creation_time.day, creation_time.hour, creation_time.minute, creation_time.second)
        hours = time_difference.total_seconds() / 3600
    else:
        hours = 0

    return b['initial']*post.punctation + b['votes']*F(f(likes, dislikes), w['post_votes']) + b['comments']*F(comments, w['post_comments']) + b['time']*F(-hours, w['post_time'])


def calculate_specific_punctation(post, user):
    ''' Funkcja, obliczająca specyficzną punktację posta dla określonego użytkownika.

    Args:
        post (common.models.Post): post dla którego liczymy punktację
        user (common.models.User): zalogowany użytkownik, dla którego liczymy punktację

    Returns:
        float: liczba rzeczywista z zakresu (-100, 100) reprezentująca specyficzną punktację dla posta
    '''
    # Oblicza średnią arytmetyczną punktacji tagów należących do posta
    tags = list(post.tags.all()) + list(post.implied_tags.all())
    tag_points = 0
    for tag in tags:
        try:
            tp = TagPunctation.objects.get(tag=tag, user=user)
            tag_points += tag_points + tp.punctation
        except TagPunctation.DoesNotExist:
            tp = TagPunctation()
            tp.user = user
            tp.tag = tag
            tp.punctation = 0
            tp.save()
            tag_points += tag_points + tp.punctation
    if tags:
        tag_points = tag_points / len(tags)

    # Pobiera ilość wyświetleń posta przez uzytkownika
    pv = PostVisit.objects.filter(post=post, user=user)
    if pv.exists():
        visit_counter = pv.first().visit_counter
    else:
        visit_counter = 0

    # Pobiera informację o tym czy użytkownik należy do sekcji z której pochodzi post
    if post.section.users.filter(login=user.login).exists():
        belongs = True
    else:
        belongs = False

    return c['tags'] * tag_points + c['visits']*F(-visit_counter, w['post_visits']) + c['belongs']*100*belongs


def calculate_specific_punctation_for_tag(initial_value, likes, dislikes, comments):
    ''' Funkcja, która oblicza specyficzną punktację dla tagu.

    Args:
        initial_value (float): obecna punktacja, którą znajduję się w bazie danych
        likes (int): ilość lajków zostawionych przez określonego użytkownika pod postami z tagiem, dla którego liczymy punktację
        dislikes (int): ilość dislajków zostawionych przez określonego użytkownika pod postami z tagiem, dla którego liczymy punktację
        comments (int): ilość komentarzy zostawionych przez określonego użytkownika pod postami z tagiem, dla którego liczymy punktację

    Returns:
        float: liczba z zakresu (-100, 100) reprezentująca statyczną punktację dla tagu
    '''
    return d['initial']*initial_value + d['votes']*F(f(likes, dislikes), w['tag_votes']) + d['comments']*F(comments, w['tag_comments'])
