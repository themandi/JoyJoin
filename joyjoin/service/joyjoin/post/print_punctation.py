""" Moduł wyświetlający dane dotyczące punktacji

Attention:
    Ten moduł zostanie przesunięty do katalogu utils.
    W żadnym wypadku nie należy go importować w serwisie.
"""

import datetime

from common.models import Post, User, TagPunctation, PostVisit, Tag, Vote, Comment
import post.punctation as P


def print_punctation_for_posts():
    """ Funkcja pomocnicza dla developerów.

    Dla każdego postu wypisuje jego punktację w rozbiciu na poszczególne czynniki. Funkcja ta nie jest w żaden sposób wywoływana w serwisie. Aby ją wywołać wystarczy użyć aliasu pp (patrz utils/set_aliases.sh)

    Returns:
        Funkcja nic nie zwraca
    """
    # Tworzy pomocnicze obiekty
    posts = list(Post.objects.all())
    current_user = User.objects.filter(login='monika').first()

    # Oblicza punktację dla każdego posta i sortuję malejąco względem tej punktacji
    posts.sort(key=lambda x: P.calculate_punctation(x, x.count_votes(
        1), x.count_votes(-1), x.count_all_comments(), current_user), reverse=True)

    # Dla każdego posta...
    for post in posts:
        # pobiera ilość lajków, dislajków komentarzy pod postem
        likes = post.count_votes(1)
        dislikes = post.count_votes(-1)
        comments = post.count_all_comments()

        # oblicza ilość godzin od publikacji posta
        creation_time = post.creation_time
        time_difference = datetime.datetime.now() - datetime.datetime(creation_time.year, creation_time.month,
                                                                      creation_time.day, creation_time.hour, creation_time.minute, creation_time.second)
        hours = time_difference.total_seconds() / 3600

        # oblicza śrędnią arytmetyczną punktacji tagów należących do posta
        tags = list(post.tags.all()) + list(post.implied_tags.all())
        tag_points = 0
        for tag in tags:
            tag_points = tag_points + \
                TagPunctation.objects.filter(
                    tag=tag, user=current_user).first().punctation
        if tags:
            tag_points = tag_points / len(tags)

        # pobiera ilość wyświetleń posta przez użytkownika
        pv = PostVisit.objects.filter(post=post, user=current_user)
        if pv.exists():
            visit_counter = pv.first().visit_counter
        else:
            visit_counter = 0

        # pobiera informację o tym czy użytkownik należy do sekcji z której pochodzi post
        if post.section.users.filter(login=current_user.login).exists():
            belongs = True
        else:
            belongs = False

        # wypisuje statystyki
        print("Post: {}".format(post.title))
        print("Statyczna punktacja (max: {}): {}".format(
            100*P.a['static'], P.a['static']*P.calculate_static_punctation(post, likes, dislikes, comments)))
        print("Specyficzna punktacja (max: {}): {}".format(
            100*P.a['specific'], P.a['specific']*P.calculate_specific_punctation(post, current_user)))
        print("Końcowa punktacja (max: 100): {}\n".format(
            P.calculate_punctation(post, likes, dislikes, comments, current_user)))

        print("Początkowa punktacja (max: {}): {}\n".format(
            100*P.a['static']*P.b['initial'], P.a['static']*P.b['initial']*post.punctation))

        print("Ilość lajków: {}".format(likes))
        print("Ilość dislajków: {}".format(dislikes))
        print("Punktacja za lajki+dislajki (max: {}): {}\n".format(100 *
                                                                   P.a['static']*P.b['votes'], P.a['static']*P.b['votes']*P.F(P.f(likes, dislikes), P.w['post_votes'])))

        print("Ilość komentarzy: {}".format(comments))
        print("Punktacja za komentarze (max: {}): {}\n".format(
            100*P.a['static']*P.b['comments'], P.a['static']*P.b['comments']*P.F(comments, P.w['post_comments'])))

        print("Ilość godzin od publikacji: {}".format(hours))
        print("Punktacja za czas publikacji (max: {}): {}\n".format(
            100*P.a['static']*P.b['time'], P.a['static']*P.b['time']*P.F(-hours, P.w['post_time'])))

        for tag in tags:
            print("Punktacja za tag {} (max: {}): {}".format(tag.name, 100*P.a['specific']*P.c['tags']*(1/len(
                tags)), P.a['specific']*P.c['tags']*(1/len(tags))*TagPunctation.objects.filter(tag=tag, user=current_user).first().punctation))
        print("Punktacja za wszystkie tagi (max: {}): {}\n".format(
            100*P.a['specific']*P.c['tags'], P.a['specific']*P.c['tags']*tag_points))

        print("Ilość wyświetleń posta przez użytkownika: {}".format(visit_counter))
        print("Punktacja za ilość wyświetleń (max: {}): {}\n".format(
            100*P.a['specific']*P.c['visits'], P.a['specific']*P.c['visits']*P.F(-visit_counter, P.w['post_visits'])))

        print("Czy użytkownik należy do sekcji z tym postem: {}".format(belongs))
        print("Punktacja za należenie do sekcji (max: {}): {}\n".format(
            100*P.a['specific']*P.c['belongs'], 100*P.a['specific']*P.c['belongs']*belongs))

        print("-"*40, "\n")


def print_punctation_for_tags():
    """ Funkcja pomocnicza dla developerów.

    Dla każdego tagu wypisuje jego punktację w rozbiciu na poszczególne czynniki. Funkcja ta nie jest w żaden sposób wywoływana w serwisie. Aby ją wywołać wystarczy użyć aliasu tp (patrz utils/set_aliases.sh)

    Returns:
        Funkcja nic nie zwraca
    """
    # Dla każdego tagu tworzy listę 3-elementową z zerami (licznik lajków, licznik dislajków, licznik komentarzy)
    stats = {}
    tags = Tag.objects.all()
    for tag in tags:
        stats[tag.id] = [0, 0, 0]
    current_user = User.objects.filter(login='monika').first()

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
        tp = TagPunctation.objects.filter(user=current_user, tag=tag).first()
        print("Tag:", tag.name)
        print("Sekcja:", tag.section.description)
        print("Obecna punktacja (zapisana w bazie danych):", tp.punctation)
        print("Ilość lajków:", stats[tag.id][0])
        print("Ilość dislajków:", stats[tag.id][1])
        print("Ilość komentarzy:", stats[tag.id][2])
        print("Nowa punktacja:", P.calculate_specific_punctation_for_tag(
            tp.punctation, stats[tag.id][0], stats[tag.id][1], stats[tag.id][2]))
        print("\n", "-"*40, "\n")
