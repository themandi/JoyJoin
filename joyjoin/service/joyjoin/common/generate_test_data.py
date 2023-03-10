"""
To jest skrypt generujący dane testowe.
Aby go uruchomić nalezy wykonać:

$ python manage.py shell -c "from common.generate_test_data import generate
generate()"
"""

from django.contrib.auth.hashers import make_password

from common.models import Post, Section, Tag, TagImplication, User, Vote, Comment, CommentVote
from report.models import Report, ReportCategory

user_prototypes = [
    ('Natalia Kowalska', 'natalia', ''),
    ('Monika Nowak', 'monika', 'Lubię programowanie w basenie oraz płonącą jengę.'),
    ('Mariusz Piwosz', 'piwosz', ''),
    ('Norbert Piłkarz', 'norbert', ''),
]

section_prototypes = [
    ('programming', 'Programowanie', ['monika', 'piwosz'], 'laptop'),
    ('soccer', 'Piłka nożna', ['piwosz', 'norbert'], 'soccer-ball'),
    ('painting', 'Malarstwo', ['natalia', 'monika', 'norbert'], 'brush'),
]

long_post_text = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Tempor id eu nisl nunc mi. Volutpat sed cras ornare arcu. Quam id leo in vitae. Eget mi proin sed libero enim sed faucibus turpis. Dignissim convallis aenean et tortor at risus viverra. Vitae congue eu consequat ac felis donec et odio. Nunc mi ipsum faucibus vitae aliquet. Velit aliquet sagittis id consectetur purus ut faucibus. Et ultrices neque ornare aenean euismod.

Morbi leo urna molestie at. Sed id semper risus in hendrerit gravida rutrum quisque non. Sit amet est placerat in egestas erat imperdiet sed. Vivamus at augue eget arcu dictum. Condimentum lacinia quis vel eros donec. Vitae turpis massa sed elementum tempus egestas sed. Massa enim nec dui nunc mattis enim. Lacinia at quis risus sed vulputate odio ut enim blandit. Duis ut diam quam nulla. Malesuada pellentesque elit eget gravida cum sociis natoque.
"""

post_prototypes = [
    ('Jak w tytule, jakie farby (od jakich producentów, jakie rodzaje) polecacie?',
     'Jakie farby olejne są najlepsze', 'natalia', 'painting', ['olej'], 'zakupy', []),
    ('Czym jest "move constructor"?', 'Move-constructor w C++11', 'monika',
     'programming', ['c++11'], 'zarządzanie-pamięcią', ['c++', 'języki', 'standardy']),
    ('Co sądzicie o naszej grupie na Euro?', 'Grupa na Euro 2020',
     'piwosz', 'soccer', [], 'mistrzostwa euro2020', []),
    (
        'Udało się! Długo się do tego zabierałem, ale w końcu wrzuciłem swoje prace do sieci. Obczajcie je pod tym linkiem: http://joyjoin.com/user/norbert/',
        'Moje prace', 'norbert', 'painting', [
            'olej', 'pastel'], 'prace', []
    ),
    (long_post_text, 'Długi post o malowaniu', 'monika', 'painting', [], '', []),
    ('Kto harata w gałę w Toruniu?', 'Meczyk',
     'norbert', 'soccer', ['spotkania'], 'toruń', []),
    ('Kto z Torunia chce spotkanie dotyczące optymalizacji w Pythonie?',
     'Spotkanie dotyczące Pythona', 'piwosz', 'programming', ['spotkania'], 'toruń', []),
    ('Poszukuję chętnej osoby do pozowania', 'Poszukiwani chętni do pozowania',
     'natalia', 'painting', ['spotkania'], 'toruń', []),
    ('To jest post testujący tagi', 'Różnice między standardami C++', 'monika',
     'programming', ['c++17', 'c++11'], '', ['c++', 'języki', 'standardy']),
    ('Zakaz komentowania w generate_test_data!', 'comment_test', 'monika',
     'programming', ['c++17', 'c++11'], '', ['c++', 'języki', 'standardy']),
]

tag_prototypes = [
    ('c++', 'programming', 'cpp', 'Język C++'),
    ('c++11', 'programming', 'cpp11', 'Standard C++11'),
    ('c++17', 'programming', 'cpp17', 'Standard C++17'),
    ('języki', 'programming', 'języki', 'Języki programowania'),
    ('standardy', 'programming', 'standardy',
     'Standardy języków programowania'),
    ('python', 'programming', '', 'Język Python'),
    ('pastel', 'painting', '', 'Pastel'),
    ('olej', 'painting', '', 'Farba olejna'),
    ('kluby', 'soccer', '', 'Kluby piłkarskie'),
    ('zasady', 'soccer', '', 'Zasady'),
    ('spotkania', 'programming', '', 'Spotkania'),
    ('spotkania', 'painting', '', 'Spotkania'),
    ('spotkania', 'soccer', '', 'Spotkania'),
]

tag_implication_prototypes = [
    ('programming', 'c++11', 'c++'),
    ('programming', 'c++17', 'c++'),
    ('programming', 'c++11', 'standardy'),
    ('programming', 'c++17', 'standardy'),
    ('programming', 'c++', 'języki'),
    ('programming', 'python', 'języki'),
]

vote_prototypes = [
    ('monika', 1, 1),
    ('norbert', 1, 1),
    ('norbert', 5, -1),
    ('monika', 8, 1),
    ('norbert', 8, -1),
    ('monika', 2, -1),
    ('piwosz', 2, 1),
]

comment_prototypes = [
    ('Ale se fajny post wstawiłem', 'norbert', 'Moje prace', '-1'), # id 1
    ('Potwierzam', 'piwosz', 'Moje prace', '1'), # id 2
    ('XD', 'monika', 'Moje prace', '-1'), # id 3
    ('No fajne te tagi', 'norbert', 'Różnice między standardami C++', '-1'), # id 4
    ('ja', 'monika', 'Poszukiwani chętni do pozowania', '-1'), # id 5
    ('jednak nie', 'monika', 'Poszukiwani chętni do pozowania', '5'), # id 6
    ('i jakby co meczyk jutro', 'norbert', 'Meczyk', '-1'), # id 7
    ('ja', 'piwosz', 'Meczyk', '-1'), # id 8
    ('super git', 'norbert', 'Meczyk', '8'), # id 9
    ('nie', 'monika', 'Moje prace', '-1'), # id 10
    ('co typ se odpisuje na swoje własne posty xD', 'monika', 'Moje prace', '1'), # id 11
    ('no co, mogę', 'norbert', 'Moje prace', '11'), # id 12
    ('XD', 'monika', 'Moje prace', '12'), # id 13
    ('XD', 'norbert', 'Moje prace', '13'), # id 14
    ('XD', 'monika', 'Moje prace', '14'), # id 15
    ('XD', 'norbert', 'Moje prace', '15'), # id 16
    ('XD', 'monika', 'Moje prace', '16'), # id 17
    ('XD', 'norbert', 'Moje prace', '17'), # id 18
    ('XDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD', 'monika', 'Moje prace', '18'), # id 19
]

comment_vote_prototypes = [
    ('monika', '1', '-1'),
    ('monika', '2', '-1'),
    ('monika', '14', '1'),
    ('monika', '19', '1'),
    ('piwosz', '1', '1'),
    ('piwosz', '7', '1'),
    ('piwosz', '9', '1'),
    ('piwosz', '12', '1'),
    ('piwosz', '19', '1'),
    ('norbert', '1', '1'),
    ('norbert', '2', '1'),
    ('norbert', '8', '1'),
    ('norbert', '19', '1'),
    ('natalia', '19', '1'),
    ('natalia', '5', '1'),
]

report_category_prototypes = [
    'Posty',
    'Komentarze',
    'Oceny',
    'Tagi',
    'Sekcje',
    'Profil użytkownika',
    'Logowanie',
    'Rejestracja',
    'Inne',
]

report_prototypes = [
    ('nie wysyła się post jak klikam wyślij', 'Posty', 'norbert'),
    ('komentarz też się nie wysyłaj jak klikam wyslij', 'Komentarze', 'norbert'),
    ('dobra nie wazne zapomnialem sie wtedy zalogowac', 'Inne', 'norbert'),
    ('Podczas scrollowania w dół z pozycji najwyższej, biały div na środku zmienia \
        rozmiar z przeciągniętego maksymalnie w dół, do rozmiaru dopasowanego do contentu wewnąrz. \
        Podobne zachowanie można zaobserwować na innych stronach tego typu. \n\nPozdrawam,\nMonika', 'Profil użytkownika', 'monika'),
    ('Nie mogę się zalogować', 'Logowanie', None),
    ('Nie mogę się zarejestrować', 'Rejestracja', None),
]


def generate():
    for model in [Post, Section, Tag, User]:
        for obj in model.objects.all():
            obj.delete()  # pragma: no cover

    for up in user_prototypes:
        user = User()
        user.name = up[0]
        user.login = up[1]
        user.password = make_password(up[1])
        user.description = up[2]
        user.email = up[1] + '@cmail.con'
        user.birth_date = '2000-01-01'
        user.save()

    for sp in section_prototypes:
        section = Section()
        section.name = sp[0]
        section.description = sp[1]
        section.icon = sp[3]
        section.save()
        for user_login in sp[2]:
            user = User.objects.filter(login=user_login).first()
            section.users.add(user)

    for tp in tag_prototypes:
        tag = Tag()
        tag.name = tp[0]
        tag.section = Section.objects.get(name=tp[1])
        if tp[2]:
            tag.slug = tp[2]
        tag.tooltip = tp[3]
        tag.save()

    for tip in tag_implication_prototypes:
        ti = TagImplication()
        section = Section.objects.get(name=tip[0])
        ti.parent = Tag.objects.get(section=section, name=tip[1])
        ti.child = Tag.objects.get(section=section, name=tip[2])
        ti.save()

    for pp in post_prototypes:
        post = Post()
        post.text = pp[0]
        post.title = pp[1]
        post.author = User.objects.filter(login=pp[2]).first()
        post.section = Section.objects.filter(name=pp[3]).first()
        if pp[5]:
            post.user_tags = pp[5]
        post.save()
        for tag in pp[4]:
            post.tags.add(Tag.objects.get(name=tag, section=post.section))
        for tag in pp[6]:
            post.implied_tags.add(Tag.objects.get(
                name=tag, section=post.section))
        post.save()

    for vp in vote_prototypes:
        vote = Vote()
        vote.user = User.objects.get(login=vp[0])
        vote.post = Post.objects.get(id=vp[1])
        vote.reaction = vp[2]
        vote.save()

    for cp in comment_prototypes:
        comment = Comment()
        comment.text = cp[0]
        comment.author = User.objects.filter(login=cp[1]).first()
        comment.parent_post = Post.objects.filter(title=cp[2]).first()
        comment.parent_comment = Comment.objects.filter(id=cp[3]).first()
        comment.save()

    for cvp in comment_vote_prototypes:
        comment_vote = CommentVote()
        comment_vote.user = User.objects.filter(login=cvp[0]).first()
        comment_vote.comment = Comment.objects.filter(id=cvp[1]).first()
        comment_vote.reaction = cvp[2]
        comment_vote.save()

    for rcp in report_category_prototypes:
        report_category = ReportCategory()
        report_category.name = rcp
        report_category.save()

    for rp in report_prototypes:
        report = Report()
        report.text = rp[0]
        report.category = ReportCategory.objects.get(name=rp[1])
        if rp[2]:
            report.user = User.objects.get(login=rp[2])
        report.save()
