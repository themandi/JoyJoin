import re

from django.test import Client, TestCase

from common.generate_test_data import generate
from common.models import Post, Tag, User
from login.tests import login_client_for_tests


valid_user_name = 'monika'  # poprawny login użytkownika testowego
# poprawna nazwa sekcji do której należy testowy użytkownik
valid_section_name = 'programming'
# poprawna nazwa innej sekcji do której należy testowy użytkownik
another_valid_section_name = 'painting'
# poprawna nazwa sekcji do której nie należy testowy użytkownik
foreign_section_name = 'soccer'
testing_post_text = '\
"<p>To jest treść posta testowego</p><p>Ma wiele linii.</p><p><br></p><p>W tym pustą (powyższą).</p>"\
' # treść przykładowego testowego posta wysyłana z formularza
testing_post_text_result = '<p>To jest treść posta testowego</p><p>Ma wiele linii.</p><p><br></p><p>W tym pustą (powyższą).</p>' # treść przykładowego testowego posta w bazie danych
testing_post_title = 'To jest tytuł posta testowego'  # tytuł przykładowego testowego posta
# przykładowa lista tagów
example_tag_list = 'cpp11 c++17 języki Honeypot🍯123 dywiz-dobry_podłoga_zła'


class CreateViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate()

    def test_create_view_with_no_user(self):
        """
        Widok powinien wyświetlać odpowiednią wiadomość dla niezalogowanego użytkownika
        """
        client = Client()
        response = client.get('/create/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Musisz się zalogować aby pisać posty')

    def test_create_view_with_user(self):
        """
        Widok powinien być dostępny dla zalogowanego użytkownika
        """
        client = Client()
        login_client_for_tests(client)
        response = client.get('/create/')
        self.assertEquals(response.status_code, 200)
        # Tutaj upewniamy się że użytkownik widzi to, co powinien widzieć jako zalogowany
        self.assertContains(response, 'Zobacz profil')

    def test_section_choice_list(self):
        """
        Lista powinna zawierać dokładnie sekcje do których należy użytkownik.
        Domyślnie wybrana powinna być sekcja, w której ostatnio był użytkownik
        """
        client = Client()
        login_client_for_tests(client)
        response = client.get('/sec/' + another_valid_section_name + '/')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            client.session['current_section_name'], another_valid_section_name)
        response = client.get('/create/')
        self.assertEquals(response.status_code, 200)

        regex_prefix = b'<select id="section_select" name="section">([\n\t]*<option value=('
        regex_suffix = b')</option>)*[\n\t]*</select>'
        user = User.objects.get(login=valid_user_name)
        section_list = []
        for sec in user.section_set.all():
            if sec.name == client.session['current_section_name']:
                selection_string = b' selected>'
            else:
                selection_string = b'>'
            section_list.append(bytes(sec.name, 'utf-8') +
                                selection_string + bytes(sec.description, 'utf-8'))
        regex_middle = b'|'.join(section_list)
        regex = regex_prefix + regex_middle + regex_suffix
        cr = re.compile(regex)
        self.assertIs(bool(cr.search(response.content)), True)


class AddViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate()

    def test_creating_a_new_post(self):
        client = Client()
        login_client_for_tests(client)
        # potrzebne żeby przetestować czy wybór użytkownika jest dobrze odbity w bazie danych
        client.get('/sec/' + another_valid_section_name + '/')
        response = client.post('/create/add/', {'title': testing_post_title,
                                                'post': testing_post_text, 'section': valid_section_name, 'tags': example_tag_list})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/all/')
        last_post_from_db = Post.objects.last()
        self.assertEquals(last_post_from_db.title, testing_post_title)
        self.assertEquals(last_post_from_db.text, testing_post_text_result)
        self.assertEquals(last_post_from_db.author.login,
                          client.session.get('logged_in_as'))
        self.assertEquals(last_post_from_db.section.name, valid_section_name)
        self.assertTrue(Tag.objects.get(
            section__name=valid_section_name, name='c++11') in last_post_from_db.tags.all())
        self.assertTrue(Tag.objects.get(
            section__name=valid_section_name, name='c++17') in last_post_from_db.tags.all())
        self.assertTrue(Tag.objects.get(section__name=valid_section_name,
                                        name='c++') in last_post_from_db.implied_tags.all())
        self.assertTrue(Tag.objects.get(section__name=valid_section_name,
                                        name='języki') in last_post_from_db.implied_tags.all())
        self.assertTrue(Tag.objects.get(section__name=valid_section_name,
                                        name='standardy') in last_post_from_db.implied_tags.all())
        self.assertTrue('honeypot123' in last_post_from_db.user_tags_as_list())
        self.assertTrue(
            'dywiz-dobry-podłoga-zła' in last_post_from_db.user_tags_as_list())

    def test_attempting_to_create_a_new_post_while_not_logged_in(self):
        client = Client()
        number_of_posts_in_db = Post.objects.count()
        response = client.post('/create/add/', {'title': testing_post_title,
                                                'post': testing_post_text, 'section': valid_section_name, 'tags': example_tag_list})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, b'B\xc5\x82\xc4\x85d sesji')
        self.assertEquals(Post.objects.count(), number_of_posts_in_db)

    def test_attempting_to_create_a_new_post_in_foreign_section(self):
        client = Client()
        login_client_for_tests(client)
        response = client.post('/create/add/', {'title': testing_post_title,
                                                'post': testing_post_text, 'section': foreign_section_name, 'tags': example_tag_list})
        self.assertEquals(response.status_code, 200)
        self.assertEquals(
            response.content, b'B\xc5\x82\xc4\x85d dodawania posta: nie nale\xc5\xbcysz do sekcji Pi\xc5\x82ka no\xc5\xbcna')

    def test_attempting_to_create_a_new_post_with_no_text(self):
        client = Client()
        login_client_for_tests(client)
        response = client.post(
            '/create/add/', {'title': testing_post_title, 'section': valid_section_name, 'tags': example_tag_list})
        self.assertEquals(response.status_code, 200)
        self.assertIs(response.content == b'B\xc5\x82\xc4\x85d POST', True)

    def test_attempting_to_create_a_new_post_with_no_title(self):
        client = Client()
        login_client_for_tests(client)
        response = client.post(
            '/create/add/', {'post': testing_post_text, 'section': valid_section_name, 'tags': example_tag_list})
        self.assertEquals(response.status_code, 200)
        self.assertIs(response.content == b'B\xc5\x82\xc4\x85d POST', True)

    def test_attempting_to_create_a_new_post_with_no_section(self):
        client = Client()
        login_client_for_tests(client)
        response = client.post(
            '/create/add/', {'title': testing_post_title, 'post': testing_post_text, 'tags': example_tag_list})
        self.assertEquals(response.status_code, 200)
        self.assertIs(response.content == b'B\xc5\x82\xc4\x85d POST', True)
