from django.test import Client, TestCase
from django.http import HttpRequest
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages import get_messages

from common.generate_test_data import generate
from login.tests import login_client_for_tests
from .views import complete

correctData = {'login': 'stachu',
               'name': 'Stanislaw',
               'email': 'stachu@wp.pl',
               'password': 'konstantynopol',
               'password_2': 'konstantynopol',
               'birth_date': '1998-01-01',
               'rules': 'on'}


class IsLoginUnusedViewTest(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_login_unused(self):
        client = Client()
        unused_login = "nikt0takiego0nie0ma"
        response = client.post('/register/is_login_unused/', {'login': unused_login})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "true")

    def test_login_used(self):
        client = Client()
        unused_login = "monika"
        response = client.post('/register/is_login_unused/', {'login': unused_login})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "false")

    def test_login_blank(self):
        client = Client()
        blank_login = ""
        response = client.post('/register/is_login_unused/', {'login': blank_login})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "false")

    def test_login_empty(self):
        client = Client()
        response = client.post('/register/is_login_unused/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "false")


class IsPasswordUncommonViewTest(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_password_uncommon(self):
        client = Client()
        uncommon_password = "qwerty123$%^"
        response = client.post('/register/is_password_uncommon/', {'password': uncommon_password})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "true")

    def test_password_common(self):
        client = Client()
        common_password = "qwerty12"
        response = client.post('/register/is_password_uncommon/', {'password': common_password})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "false")

    def test_password_blank(self):
        client = Client()
        blank_password = ""
        response = client.post('/register/is_password_uncommon/', {'password': blank_password})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "false")

    def test_password_empty(self):
        client = Client()
        response = client.post('/register/is_password_uncommon/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "false")


class IsAgeOkViewTest(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_age_ok(self):
        client = Client()
        birth_date = "2002-03-23"
        response = client.post('/register/is_age_ok/', {'date': birth_date})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "true")

    def test_age_not_ok(self):
        client = Client()
        birth_date = "2010-03-23"
        response = client.post('/register/is_age_ok/', {'date': birth_date})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "false")

    def test_age_blank(self):
        client = Client()
        blank_birth_date = ""
        response = client.post('/register/is_age_ok/', {'date': blank_birth_date})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "false")

    def test_age_empty(self):
        client = Client()
        response = client.post('/register/is_age_ok/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "false")


class RegisterViewTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_register_view(self):
        client = Client()
        response = client.get('/register/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Rejestracja')
        self.assertContains(response, 'REJESTRUJ')
        self.assertContains(response, 'Akceptuję regulamin')

    def test_login_view_for_logged_user(self):
        client = Client()
        login_client_for_tests(client)
        response = client.get('/register/')
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/all/')


class VerifyViewTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_complete_on_correct_data(self):
        client = Client()
        response = client.post('/register/complete/', correctData)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/register/')

    def test_complete_on_correct_data_with_follow(self):
        client = Client()
        response = client.post('/register/complete/', correctData, follow=True)
        self.assertEquals(response.status_code, 200)
        for msg in response.context['messages']:
            self.assertEquals(
                msg.message, 'Dziękujemy za założenie konta! Zapraszamy do korzystania z JoyJoin!')

    def test_complete_on_incorrect_data(self):
        client = Client()
        incorrectData = correctData.copy()
        incorrectData['password_2'] = 'bizancjum'
        response = client.post('/register/complete/', incorrectData)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/register/')

    def test_complete_on_incorrect_data_with_follow(self):
        client = Client()
        incorrectData = correctData.copy()
        incorrectData['password_2'] = 'bizancjum'
        response = client.post('/register/complete/',
                               incorrectData, follow=True)
        self.assertEquals(response.status_code, 200)
        for msg in response.context['messages']:
            self.assertEquals(msg.message, 'Hasła nie są identyczne')

    def test_complete_on_missing_post_data(self):
        client = Client()
        incorrectData = correctData.copy()
        del incorrectData['email']
        response = client.post('/register/complete/',
                               incorrectData, follow=True)
        self.assertEquals(response.status_code, 200)
        for msg in response.context['messages']:
            self.assertEquals(msg.message, 'Błąd POST')
        self.assertContains(response, 'Błąd POST')


class RegisterTests(TestCase):
    correctData = correctData

    def single_test(self, data, expectedResult):
        # utworzenie nowego zapytania
        request = HttpRequest()
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)
        request.POST = data

        # sprawdzenie poprawności danych
        complete(request)

        # wypisanie komunikatu w przypadku blednego zachowania funkcji
        for message in get_messages(request):
            assert message.extra_tags is expectedResult, message.extra_tags + \
                " " + str(request.POST)

    # Testy loginu

    def test_login_with_correct_data(self):
        data = self.correctData.copy()
        self.single_test(data, 'OK')
        data['login'] = 'eluwina'
        self.single_test(data, 'OK')
        data['login'] = 'xyz'
        self.single_test(data, 'OK')
        data['login'] = 'xxxxxxxxxxxxxxxxxxxx'
        self.single_test(data, 'OK')
        data['login'] = 'jankowalski'
        self.single_test(data, 'OK')

    def test_login_with_too_short_login(self):
        data = self.correctData.copy()
        data['login'] = 'xd'
        self.single_test(data, 'login_wrong_length')
        data['login'] = 'x'
        self.single_test(data, 'login_wrong_length')
        data['login'] = ''
        self.single_test(data, 'login_wrong_length')

    def test_login_with_too_long_login(self):
        data = self.correctData.copy()
        data['login'] = 'aaaaabbbbbcccccddddde'
        self.single_test(data, 'login_wrong_length')
        data['login'] = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        self.single_test(data, 'login_wrong_length')

    def test_login_with_forbidden_characters(self):
        data = self.correctData.copy()
        data['login'] = 'ja pie*dole'
        self.single_test(data, 'login_forbidden_characters')
        data['login'] = 'jan kowalski'
        self.single_test(data, 'login_forbidden_characters')

    def test_login_with_forbidden_first_character(self):
        data = self.correctData.copy()
        data['login'] = '_login'
        self.single_test(data, 'login_forbidden_first_character')
        data['login'] = '5kazimierz'
        self.single_test(data, 'login_forbidden_first_character')

    def test_login_with_used_login(self):
        self.test_login_with_correct_data()
        data = self.correctData.copy()
        self.single_test(data, 'login_used')
        data['login'] = 'eluwina'
        self.single_test(data, 'login_used')
        data['login'] = 'xyz'
        self.single_test(data, 'login_used')
        data['login'] = 'xxxxxxxxxxxxxxxxxxxx'
        self.single_test(data, 'login_used')
        data['login'] = 'jankowalski'
        self.single_test(data, 'login_used')

    # Testy nazwiska
    def test_name_with_correct_data(self):
        data = self.correctData.copy()
        data['name'] = 'Jan Kowalski'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['name'] = 'Andrzej Nowak'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['name'] = 'xyz'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['name'] = 'Miłosz'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['name'] = 'Konstantypolitańczykowianeczka czy jakoś tak'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['name'] = 'abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi abc'
        self.single_test(data, 'OK')

    def test_name_with_too_short_name(self):
        data = self.correctData.copy()
        data['name'] = 'xD'
        self.single_test(data, 'name_wrong_length')
        data['name'] = 'x'
        self.single_test(data, 'name_wrong_length')
        data['name'] = ''
        self.single_test(data, 'name_wrong_length')

    def test_name_with_too_long_name(self):
        data = self.correctData.copy()
        data['name'] = 'abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi abcdefghi abcd'
        self.single_test(data, 'name_wrong_length')
        data['name'] = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
        self.single_test(data, 'name_wrong_length')
        data['name'] = 'xDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD'
        self.single_test(data, 'name_wrong_length')

    def test_name_with_forbidden_characters(self):
        data = self.correctData.copy()
        data['name'] = '*******'
        self.single_test(data, 'name_forbidden_characters')
        data['name'] = '_!()[]"fsdf"\'\''
        self.single_test(data, 'name_forbidden_characters')
        data['name'] = '\'\'\'\'\'\''
        self.single_test(data, 'name_forbidden_characters')
        data['name'] = '""""""'
        self.single_test(data, 'name_forbidden_characters')

    # Testy hasla
    def test_password_with_correct_data(self):
        data = self.correctData.copy()
        data['password'] = data['password_2'] = 'haslohaslo'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['password'] = data['password_2'] = 'eluwinax'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['password'] = data['password_2'] = 'sdnfsdnfksjdn!@!#!$1235646589'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['password'] = data['password_2'] = 'xddddddddddddddddd'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['password'] = data['password_2'] = '!!!!!!!!!!!!!!!'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['password'] = data['password_2'] = 'asdfghjkl123123123'
        self.single_test(data, 'OK')

    def test_password_with_too_short_password(self):
        data = self.correctData.copy()
        data['password'] = data['password_2'] = 'eluwina'
        self.single_test(data, 'password_too_short')
        data['password'] = data['password_2'] = 'unodos'
        self.single_test(data, 'password_too_short')
        data['password'] = data['password_2'] = ''
        self.single_test(data, 'password_too_short')
        data['password'] = data['password_2'] = '?'
        self.single_test(data, 'password_too_short')

    def test_password_with_too_common_password(self):
        data = self.correctData.copy()
        data['password'] = data['password_2'] = 'qwertyuiop'
        self.single_test(data, 'password_too_common')
        data['password'] = data['password_2'] = 'asdfghjkl'
        self.single_test(data, 'password_too_common')
        data['password'] = data['password_2'] = 'administrator'
        self.single_test(data, 'password_too_common')
        data['password'] = data['password_2'] = 'admin123'
        self.single_test(data, 'password_too_common')
        data['password'] = data['password_2'] = '123456789'
        self.single_test(data, 'password_too_common')

    def test_password_with_numeric_password(self):
        data = self.correctData.copy()
        data['password'] = data['password_2'] = '42684268'
        self.single_test(data, 'password_is_numeric')
        data['password'] = data['password_2'] = '999999999999999'
        self.single_test(data, 'password_is_numeric')
        data['password'] = data['password_2'] = '2565121024'
        self.single_test(data, 'password_is_numeric')

    # Testy daty urodzenia
    def test_date_with_correct_data(self):
        data = self.correctData.copy()
        data['birth_date'] = '2001-01-01'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['birth_date'] = '1998-12-01'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['birth_date'] = '1900-12-31'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['birth_date'] = '2008-01-01'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['birth_date'] = '2004-02-29'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['birth_date'] = '1996-02-29'
        self.single_test(data, 'OK')
        data['login'] += '_'
        data['birth_date'] = '1999-5-1'
        self.single_test(data, 'OK')

    def test_date_with_wrong_format(self):
        data = self.correctData.copy()
        data['birth_date'] = '2001-13-01'
        self.single_test(data, 'age_wrong_format')
        data['birth_date'] = '1998/12/01'
        self.single_test(data, 'age_wrong_format')
        data['birth_date'] = '1900-12-31 11:50:50'
        self.single_test(data, 'age_wrong_format')
        data['birth_date'] = '19999/05/20'
        self.single_test(data, 'age_wrong_format')
        data['birth_date'] = '1999-04-31'
        self.single_test(data, 'age_wrong_format')
        data['birth_date'] = '1995-02-29'
        self.single_test(data, 'age_wrong_format')
        data['birth_date'] = '199-01-01'
        self.single_test(data, 'age_wrong_format')

    def test_date_when_too_young(self):
        data = self.correctData.copy()
        data['birth_date'] = '2009-12-01'
        self.single_test(data, 'age_wrong_date')
        data['birth_date'] = '2015-11-01'
        self.single_test(data, 'age_wrong_date')
        data['birth_date'] = '2020-01-09'
        self.single_test(data, 'age_wrong_date')
        data['birth_date'] = '2050-12-01'
        self.single_test(data, 'age_wrong_date')

    def test_date_when_too_old(self):
        data = self.correctData.copy()
        data['birth_date'] = '1800-12-01'
        self.single_test(data, 'age_wrong_date')
        data['birth_date'] = '1750-11-01'
        self.single_test(data, 'age_wrong_date')
        data['birth_date'] = '0199-01-09'
        self.single_test(data, 'age_wrong_date')
        data['birth_date'] = '0111-12-01'
        self.single_test(data, 'age_wrong_date')

    # Testy regulaminu

    def test_rules_with_correct_data(self):
        data = self.correctData.copy()
        data['rules'] = 'on'
        self.single_test(data, 'OK')

    def test_rules_not_accepted(self):
        data = self.correctData.copy()
        data['rules'] = 'off'
        self.single_test(data, 'rules_not_accepted')
        data['rules'] = 'no'
        self.single_test(data, 'rules_not_accepted')
        data['rules'] = ''
        self.single_test(data, 'rules_not_accepted')
        data['rules'] = 'xd'
        self.single_test(data, 'rules_not_accepted')
