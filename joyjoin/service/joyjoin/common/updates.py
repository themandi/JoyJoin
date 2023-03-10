""" Moduł aktualizujący tabele PostVisit i TagPunctation

Moduł zawierający funkcje do aktualizacji tabeli PostVisit oraz tabeli TagPunctation.

"""
from datetime import datetime

from common.models import Tag, Comment, PostVisit, TagPunctation, Vote
from post.punctation import calculate_specific_punctation_for_tag


def update_post_visits(posts_to_display, current_user):
    """ Funkcja, która aktualizuję tabelę PostVisit.

    Wywoływana tylko z funkcji get_posts().

    Args:
        posts_to_display (list(tuple)): lista krotek (istotny jest tylko pierwszy element krotki) z postami, które są aktualnie wysyłane do użytkownika
        current_user (common.models.User): aktualnie zalogowany użytkownik

    Returns:
        Funkcja nic nie zwraca

    Note:
        Pierwszy argument funkcji jest listą krotek, ale istotny jest tylko pierwszy element krotki, który jest postem (common.models.Post). Pozostałe elementy krotki nie są uwzględniane. Wiąże się to z tym, że  w funkcji get_post() posty znajdują się w krotkach razem z informacją o lajkach, dislajkach i komentarzach.
    """
    for post in posts_to_display:
        post = post[0]
        pv = PostVisit.objects.filter(post=post, user=current_user)
        if pv.exists():
            pv = pv.first()
            pv.visit_counter = pv.visit_counter + 1
        else:
            pv = PostVisit()
            pv.post = post
            pv.user = current_user
            pv.visit_counter = 1
        pv.save()


def update_tag_punctations(current_user, check_conditions=True):
    """ Funkcja, która aktualizuję tabelę TagPunctation.

    Aktualizuje następuje, gdy użytkownik na to zezwolił oraz upłynęło odpowiednio wiele czasu. Wywoływana tylko z funkcji get_posts().

    Args:
        current_user (common.models.User): aktualnie zalogowany użytkownik
        check_conditions (bool): True, jeżeli chcemy przed wykonaniem logiki funkcji sprawdzić warunki (czy użytkownik na to pozwala i czy upłynęło odpowiednio wiele czasu), False, jeżeli chcemy to wykonać mimo wszystko

    Returns:
        Funkcja nic nie zwraca
    """
    # Oblicza czas, który upłynął od ostatniej aktualizacji
    update_time = current_user.last_update_punctation_time
    time_difference = datetime.now() - datetime(update_time.year, update_time.month,
                                                update_time.day, update_time.hour, update_time.minute, update_time.second)

    # Jezeli użytkownik zezwola na zmianę punktacji oraz upłynęło odpowiednio wiele czasu...
    if check_conditions is False or (current_user.is_punctation_changeable is True and time_difference.total_seconds() > 24*60*60):
        # Dla każdego tagu tworzy listę 3-elementową z zerami (licznik lajków, licznik dislajków, licznik komentarzy)
        stats = {}
        tags = Tag.objects.all()
        for tag in tags:
            stats[tag.id] = [0, 0, 0]

        # Dla każdego głosu oddanego przez użytkownika...
        for vote in Vote.objects.filter(user=current_user):
            # Dla każdego tagu, który posiada oceniony post...
            for tag in list(vote.post.tags.all()) + list(vote.post.implied_tags.all()):
                # Zwiększa odpowiedni licznik w zależności czy to był lajk czy dislajk
                if vote.reaction == 1:
                    stats[tag.id][0] = stats[tag.id][0] + 1
                else:
                    stats[tag.id][1] = stats[tag.id][1] + 1

        # Dla każdego komentarza oddanego przez użytkownika...
        for comment in Comment.objects.filter(author=current_user):
            # Dla każdego tagu, który posiada skomentowany post...
            for tag in list(comment.parent_post.tags.all()) + list(comment.parent_post.implied_tags.all()):
                # Zwiększa licznik komentarzy
                stats[tag.id][2] = stats[tag.id][2] + 1

        # Dla każdego tagu...
        for tag in tags:
            # Wylicza punktacje na podstawie obliczonych liczników i zapisuje w tabeli TagPunctation
            try:
                tp = TagPunctation.objects.get(user=current_user, tag=tag)
                tp.punctation = calculate_specific_punctation_for_tag(
                    tp.punctation, stats[tag.id][0], stats[tag.id][1], stats[tag.id][2])
                tp.save()
            except TagPunctation.DoesNotExist:
                tp = TagPunctation()
                tp.user = current_user
                tp.tag = tag
                tp.punctation = calculate_specific_punctation_for_tag(
                    0, stats[tag.id][0], stats[tag.id][1], stats[tag.id][2])
                tp.save()

        # Aktualizuje czas ostatniej zmiany punktacji
        current_user.update_last_update_punctation_time()
