from django.test import Client, TestCase
import re

from common.generate_test_data import generate
from common.models import Comment, CommentVote, Post, Section, Tag, User
from login.tests import login_client_for_tests, test_user_username
from sec.comments import get_comments_list


valid_nonexistent_section_name = 'fast-cars'
valid_section_name = 'programming'
valid_section_name_with_test_user = 'programming'
valid_section_name_without_test_user = 'soccer'

tag_test_section_name = valid_section_name
tag_test_tag_in_test_section = 'standardy'
tag_test_tag_slug_in_test_section = 'cpp11'
tag_test_user_tag_in_test_section = 'zarządzanie-pamięcią'
tag_test_tag_not_in_test_section = 'i-do-not-exist'


commentless_post_title = 'comment_test'
one_comment_post_title = 'Różnice między standardami C++'


class GetCommentsListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate()

    def test_get_comments_list_with_no_comments(self):
        post = Post.objects.get(title=commentless_post_title)
        user = User.objects.first()
        result = []
        self.assertEquals(get_comments_list(post, user), result)

    def test_get_comments_list_with_one_top_lvl_comment(self):
        post = Post.objects.get(title=one_comment_post_title)
        user = User.objects.first()
        comment = Comment.objects.get(parent_post=post)
        result = [(comment, 0, 0, False, False)]
        self.assertEquals(get_comments_list(post, user), result)

    def test_get_comments_list_with_some_top_lvl_comment(self):
        post = Post.objects.get(title=commentless_post_title)
        user = User.objects.first()
        comment1 = Comment(parent_post=post)
        comment1.save()
        comment2 = Comment(parent_post=post)
        comment2.save()
        result = [(comment1, 0, 0, False, False),
                  (comment2, 0, 0, False, False)]
        self.assertEquals(get_comments_list(post, user), result)

    def test_get_comments_list_with_advanced_structure(self):
        post = Post.objects.get(title=commentless_post_title)
        user = User.objects.get(id=1)
        another_user = User.objects.get(id=2)

        comment1 = Comment(parent_post=post, author=user)
        comment1.save()
        comment2 = Comment(parent_post=post, author=user)
        comment2.save()
        comment3 = Comment(parent_post=post, author=user)
        comment3.save()
        comment4 = Comment(
            parent_post=post, parent_comment=comment1, author=user)
        comment4.save()

        comment_vote1 = CommentVote(user=user, comment=comment1, reaction=1)
        comment_vote2 = CommentVote(user=user, comment=comment3, reaction=-1)
        comment_vote3 = CommentVote(
            user=another_user, comment=comment1, reaction=1)
        comment_vote4 = CommentVote(
            user=another_user, comment=comment2, reaction=1)
        comment_vote5 = CommentVote(
            user=another_user, comment=comment3, reaction=1)
        comment_vote1.save()
        comment_vote2.save()
        comment_vote3.save()
        comment_vote4.save()
        comment_vote5.save()

        result = [
            (comment1, 2, 0, True, False),
            (comment2, 1, 0, False, False),
        ]
        self.assertEquals(get_comments_list(post, user), result)

    def test_get_comments_list_with_advanced_structure_and_no_user(self):
        post = Post.objects.get(title=commentless_post_title)
        user = User.objects.get(id=1)
        another_user = User.objects.get(id=2)

        comment1 = Comment(parent_post=post, author=user)
        comment1.save()
        comment2 = Comment(parent_post=post, author=user)
        comment2.save()
        comment3 = Comment(parent_post=post, author=user)
        comment3.save()
        comment4 = Comment(
            parent_post=post, parent_comment=comment1, author=user)
        comment4.save()

        comment_vote1 = CommentVote(user=user, comment=comment1, reaction=1)
        comment_vote2 = CommentVote(user=user, comment=comment3, reaction=-1)
        comment_vote3 = CommentVote(
            user=another_user, comment=comment1, reaction=1)
        comment_vote4 = CommentVote(
            user=another_user, comment=comment2, reaction=1)
        comment_vote5 = CommentVote(
            user=another_user, comment=comment3, reaction=1)
        comment_vote1.save()
        comment_vote2.save()
        comment_vote3.save()
        comment_vote4.save()
        comment_vote5.save()

        result = [
            (comment1, 2, 0, False, False),
            (comment2, 1, 0, False, False),
        ]
        self.assertEquals(get_comments_list(post, None), result)


class SectionViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate()

    def test_section_view_for_nonexistent_section(self):
        client = Client()
        response = client.get('/sec/' + valid_nonexistent_section_name + '/')
        self.assertEqual(response.status_code, 404)

    def test_section_view_for_no_logged_user(self):
        client = Client()
        response = client.get('/sec/' + valid_section_name + '/')

        # Testuje odpowiedź HTTP
        self.assertEquals(response.status_code, 200)

        # Testuje kontekst
        self.assertIs(response.context['this_is_the_all_view'], False)
        self.assertIs(response.context['this_is_section_view'], True)
        self.assertIs(
            response.context['current_user_in_current_section'], False)
        self.assertEquals(response.context['section_name'], valid_section_name)

        # Testuje zawartość strony
        self.assertContains(response, 'Lista sekcji')
        self.assertContains(response, 'Zobacz więcej')

    def test_section_view_for_user_logged_in_and_in_section(self):
        client = Client()
        login_client_for_tests(client)
        response = client.get(
            '/sec/' + valid_section_name_with_test_user + '/')

        # Testuje odpowiedź HTTP
        self.assertEquals(response.status_code, 200)

        # Testuje kontekst
        self.assertIs(response.context['this_is_the_all_view'], False)
        self.assertIs(response.context['this_is_section_view'], True)
        self.assertIs(
            response.context['current_user_in_current_section'], True)
        self.assertEquals(
            response.context['section_name'], valid_section_name_with_test_user)

        # Testuje zawartość strony
        self.assertContains(response, 'Twoje sekcje')
        self.assertContains(response, 'Lista sekcji')
        self.assertContains(response, 'Napisz post')
        self.assertContains(response, 'Opuść tą sekcję')
        self.assertContains(response, 'Zobacz więcej')

    def test_section_view_for_user_logged_in_and_not_in_section(self):
        client = Client()
        login_client_for_tests(client)
        response = client.get(
            '/sec/' + valid_section_name_without_test_user + '/')

        # Testuje odpowiedź HTTP
        self.assertEquals(response.status_code, 200)

        # Testuje kontekst
        self.assertIs(response.context['this_is_the_all_view'], False)
        self.assertIs(response.context['this_is_section_view'], True)
        self.assertIs(
            response.context['current_user_in_current_section'], False)
        self.assertEquals(
            response.context['section_name'], valid_section_name_without_test_user)

        # Testuje zawartość strony
        self.assertContains(response, 'Twoje sekcje')
        self.assertContains(response, 'Lista sekcji')
        self.assertContains(response, 'Napisz post')
        self.assertContains(response, 'Dołącz do tej sekcji')
        self.assertContains(response, 'Zobacz więcej')


class SectionMembershipChangeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate()

    def test_joining_section(self):
        client = Client()

        # loguje objekt 'client' jako użytkownik 'test_user_username'
        login_client_for_tests(client)

        # sprawdza że użytkownika nie ma dotąd w sekcji
        user = User.objects.get(login=test_user_username)
        section = Section.objects.get(
            name=valid_section_name_without_test_user)
        self.assertIs(user in section.users.all(), False)

        # prosi o dołączenie do sekcji przez URL
        response = client.get(
            '/sec/join/' + valid_section_name_without_test_user + '/')

        # sprawdza odpowiedź
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/sec/' +
                          valid_section_name_without_test_user + '/')

        # sprawdza że użytkownik jest już w sekcji
        section.refresh_from_db()
        self.assertIs(user in section.users.all(), True)

    def test_leaving_section(self):
        client = Client()

        # loguje objekt 'client' jako użytkownik 'test_user_username'
        login_client_for_tests(client)

        # sprawdza że użytkownik jest w sekcji
        user = User.objects.get(login=test_user_username)
        section = Section.objects.get(name=valid_section_name_with_test_user)
        self.assertIs(user in section.users.all(), True)

        # prosi o dołączenie do sekcji przez URL
        response = client.get(
            '/sec/leave/' + valid_section_name_with_test_user + '/')

        # sprawdza odpowiedź
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/sec/' +
                          valid_section_name_with_test_user + '/')

        # sprawdza że użytkownika nie ma już w sekcji
        section.refresh_from_db()
        self.assertIs(user in section.users.all(), False)

    def test_filter_by_tag(self):
        tag = tag_test_tag_in_test_section
        client = Client()

        # prosi o stronę sekcji testowej filtrowaną po tagu testowym
        response = client.get('/sec/' + tag_test_section_name + '/?tag=' + tag)

        for post in response.context['posts_to_display']:
            self.assertTrue(post[0].tags.filter(name=tag)
                            or post[0].implied_tags.filter(name=tag))

    def test_filter_by_tag_slug(self):
        slug = tag_test_tag_slug_in_test_section
        client = Client()

        # prosi o stronę sekcji testowej filtrowaną po tagu testowym
        response = client.get(
            '/sec/' + tag_test_section_name + '/?tag=' + slug)

        for post in response.context['posts_to_display']:
            self.assertTrue(post[0].tags.filter(slug=slug)
                            or post[0].implied_tags.filter(slug=slug))

    def test_filter_by_user_tag(self):
        tag = tag_test_user_tag_in_test_section
        client = Client()

        # prosi o stronę sekcji testowej filtrowaną po tagu testowym
        response = client.get('/sec/' + tag_test_section_name + '/?tag=' + tag)

        for post in response.context['posts_to_display']:
            self.assertTrue(tag in post[0].user_tags_as_list())

    def test_filter_by_nonexistent_tag(self):
        tag = tag_test_tag_not_in_test_section
        client = Client()

        # prosi o stronę sekcji testowej filtrowaną po tagu testowym
        response = client.get('/sec/' + tag_test_section_name + '/?tag=' + tag)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/sec/' + tag_test_section_name + '/')


class TagViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate()

    def test_tag_display(self):
        client = Client()

        # prosi o stronę tagów sekcji testowej
        response = client.get('/sec/' + tag_test_section_name + '/tags/')

        # sprawdza odpowiedź
        self.assertEqual(response.status_code, 200)
        cr = re.compile(b'<ul id="tag_list">.*</ul>', flags=re.DOTALL)
        result = cr.search(response.content)
        self.assertTrue(result)
        span = result.span()
        list_html = response.content[span[0]:span[1]]
        cr = re.compile(
            b'<li><a[ \n\t]*class=[\'"][a-z]+[\'"].*?</a>.*?</li>', flags=re.DOTALL)
        iterator = cr.finditer(list_html)
        html_tag_list = []
        for tag in iterator:
            html_tag_list.append(tag)
        # liczba tagów wyświetlanych w sekcji
        self.assertEqual(len(html_tag_list), 8)
        type_tag_regex = re.compile(b'<li><a[ \n\t]*class=[\'"]tag[\'"]')
        type_usertag_regex = re.compile(
            b'<li><a[ \n\t]*class=[\'"]usertag[\'"]')
        name_regex = re.compile(b'>.*?</a>')
        popularity_regex = re.compile(b'(\\([1-9][0-9]*\\)|0)')
        previous_tag_popularity = -1
        for tag in html_tag_list:
            matched_string = tag.string[tag.start():tag.end()]
            # określamy typ tagu
            tag_type = ''
            if type_tag_regex.match(matched_string):
                tag_type = 'tag'
            if type_usertag_regex.match(matched_string):
                # upewniamy się że tag nie został sklasyfikowany podwójnie
                self.assertFalse(tag_type)
                tag_type = 'usertag'
            # upewniamy się że tag został sklasyfikowany w jeden ze sposobów
            self.assertTrue(tag_type)
            tag_name = ''
            result = name_regex.search(matched_string[4:])
            self.assertTrue(result)
            tag_name = matched_string[result.span(
            )[0] + 1 + 4:result.span()[1] - 4 + 4]
            self.assertTrue(tag_name)
            tag_popularity = 0
            result = popularity_regex.search(matched_string)
            self.assertTrue(result)
            tag_popularity = int(matched_string[result.span()[
                                 0] + 1:result.span()[1] - 1])
            self.assertFalse(previous_tag_popularity >=
                             0 and previous_tag_popularity < tag_popularity)
            previous_tag_popularity = tag_popularity
            if tag_type == 'tag':
                tag_from_db = Tag.objects.filter(
                    name=str(tag_name, 'utf-8'), section__name=tag_test_section_name)
                self.assertTrue(tag_from_db)
            elif tag_type == 'usertag':
                found = False
                for post in Post.objects.filter(section__name=tag_test_section_name):
                    for usertag in post.user_tags_as_list():
                        if usertag == str(tag_name, 'utf-8'):
                            found = True
                self.assertTrue(found)


class PreferencesViewTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_preferences_view_for_all(self):
        client = Client()
        login_client_for_tests(client)

        response = client.get('/all/preferences')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Preferencje')
        self.assertContains(response, 'c++')
        self.assertContains(response, 'kluby')
        self.assertContains(response, 'olej')
        self.assertContains(response, 'Pozwalaj algorytmowi')
        self.assertContains(response, 'Ostatnia modyfikacja')
        self.assertContains(response, '<input type="submit" value="Zapisz">')
        self.assertContains(response, '<span id="counter_7" class="counter">0</span>')

    def test_preferences_view_for_all_after_updating_tag_punctations(self):
        client = Client()
        login_client_for_tests(client)

        response = client.post('/sec/all/update_punctation/', {'7': 5})
        self.assertEquals(response.status_code, 302)

        response = client.get('/all/preferences')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Preferencje')
        self.assertContains(response, 'c++')
        self.assertContains(response, 'kluby')
        self.assertContains(response, 'olej')
        self.assertContains(response, 'Pozwalaj algorytmowi')
        self.assertContains(response, 'Ostatnia modyfikacja')
        self.assertContains(response, '<input type="submit" value="Zapisz">')
        self.assertContains(response, '<span id="counter_7" class="counter">5</span>')

    def test_preferences_view_for_programming(self):
        client = Client()
        login_client_for_tests(client)

        response = client.get('/sec/programming/preferences/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Preferencje')
        self.assertContains(response, 'c++')
        self.assertContains(response, 'Pozwalaj algorytmowi')
        self.assertContains(response, 'Ostatnia modyfikacja')
        self.assertContains(response, '<input type="submit" value="Zapisz">')
        self.assertContains(response, '<span id="counter_2" class="counter">0</span>')

    def test_preferences_view_for_programming_after_updating_tag_punctations(self):
        client = Client()
        login_client_for_tests(client)

        response = client.post('/sec/programming/update_punctation/', {'2': 10})
        self.assertEquals(response.status_code, 302)

        response = client.get('/sec/programming/preferences/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Preferencje')
        self.assertContains(response, 'c++')
        self.assertContains(response, 'Pozwalaj algorytmowi')
        self.assertContains(response, 'Ostatnia modyfikacja')
        self.assertContains(response, '<input type="submit" value="Zapisz">')
        self.assertContains(response, '<span id="counter_2" class="counter">10</span>')

    def test_preferences_view_for_soccer(self):
        client = Client()
        login_client_for_tests(client)

        response = client.get('/sec/soccer/preferences/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Preferencje')
        self.assertContains(response, 'kluby')
        self.assertContains(response, 'Pozwalaj algorytmowi')
        self.assertContains(response, 'Ostatnia modyfikacja')
        self.assertContains(response, '<input type="submit" value="Zapisz">')
        self.assertContains(response, '<span id="counter_10" class="counter">0</span>')

    def test_preferences_view_for_soccer_after_updating_tag_punctations(self):
        client = Client()
        login_client_for_tests(client)

        response = client.post('/sec/soccer/update_punctation/', {'10': -3})
        self.assertEquals(response.status_code, 302)

        response = client.get('/sec/soccer/preferences/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Preferencje')
        self.assertContains(response, 'kluby')
        self.assertContains(response, 'Pozwalaj algorytmowi')
        self.assertContains(response, 'Ostatnia modyfikacja')
        self.assertContains(response, '<input type="submit" value="Zapisz">')
        self.assertContains(response, '<span id="counter_10" class="counter">-3</span>')

    def test_preferences_view_for_painting(self):
        client = Client()
        login_client_for_tests(client)

        response = client.get('/sec/painting/preferences/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Preferencje')
        self.assertContains(response, 'olej')
        self.assertContains(response, 'Pozwalaj algorytmowi')
        self.assertContains(response, 'Ostatnia modyfikacja')
        self.assertContains(response, '<input type="submit" value="Zapisz">')
        self.assertContains(response, '<span id="counter_12" class="counter">0</span>')

    def test_preferences_view_for_painting_after_updating_tag_punctations(self):
        client = Client()
        login_client_for_tests(client)

        response = client.post('/sec/painting/update_punctation/', {'12': '-5'})
        self.assertEquals(response.status_code, 302)

        response = client.get('/sec/painting/preferences/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Preferencje')
        self.assertContains(response, 'olej')
        self.assertContains(response, 'Pozwalaj algorytmowi')
        self.assertContains(response, 'Ostatnia modyfikacja')
        self.assertContains(response, '<input type="submit" value="Zapisz">')
        self.assertContains(response, '<span id="counter_12" class="counter">-5</span>')
