from django.test import Client, TestCase

from common.generate_test_data import generate


valid_username = 'monika'
valid_email = 'monika@cmail.com'
wrong_email = 'akinom@cmail.com'
test_user_username = valid_username  # alias dla lepszego kontekstu
wrong_username = 'tinsu'  # There Is No Such User
valid_user_password = 'monika'
wrong_user_password = 'monika2'


def login_client_for_tests(client, login_method='login'):
    """ Funkcja pomocnicza logująca użytkownika.

    Należy jej używać zamiast ręcznie logować użytkownika.
    Służy tylko do testów: żaden kod produkcyjny nie powininen importować niczego z plików testowych.
    Należy zadbać o wykonanie common.generate_test_data.generate() przed wywołaniem tej funkcji.

    Args:
        client (django.test.Client): klient testowy Django
        login_method (str): metoda logowania, patrz niżej

    Note:
        Dozwolone metody logowania to
            - 'login' -- loguje użytkownika przy użyciu loginu
            - 'email' -- loguje użytkownika przy użyciu emaila

    Raises:
        ValueEror: kiedy wybrano złą metodę logowania
    """
    if login_method not in ['login', 'email']:
        raise ValueError('Wybrano złą metodę logowania')
    if login_method == 'login':
        client.post('/login/verify/',
                    {'login': valid_username, 'password': valid_user_password})
    elif login_method == 'email':
        client.post('/login/verify/',
                    {'login': valid_email, 'password': valid_user_password})


class LoginViewTests(TestCase):
    @classmethod
    def setUpTestData(self):
        generate()

    def test_login_view_reachable(self):
        client = Client()
        response = client.get('/login/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Logowanie')
        self.assertContains(response, 'Zaloguj')

    def test_login_view_for_logged_user(self):
        client = Client()
        login_client_for_tests(client)
        response = client.get('/login/')
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/all/')


class VerifyViewTests(TestCase):
    @classmethod
    def setUpTestData(self):
        generate()

    def test_login_with_email_verification_wrong_password(self):
        client = Client()
        response = client.post(
            '/login/verify/', {'login': valid_email, 'password': wrong_user_password})
        self.assertEquals(response.status_code, 302)
        self.assertIs(client.session.get('logged_in_as'), None)

    def test_login_verification_wrong_email(self):
        client = Client()
        response = client.post(
            '/login/verify/', {'login': wrong_email, 'password': valid_user_password})
        self.assertEquals(response.status_code, 302)
        self.assertIs(client.session.get('logged_in_as'), None)

    def test_login_verification_with_missing_email(self):
        client = Client()
        response = client.post(
            '/login/verify/', {'password': valid_user_password})
        self.assertEquals(response.status_code, 200)
        self.assertIs(response.content ==
                      b'Wyst\xc4\x85pi\xc5\x82 b\xc5\x82\xc4\x85d podczas logowania: b\xc5\x82\xc4\x85d POST', True)

    def test_login_with_email_verification_with_missing_password(self):
        client = Client()
        response = client.post('/login/verify/', {'login': wrong_username})
        self.assertEquals(response.status_code, 200)
        self.assertIs(response.content ==
                      b'Wyst\xc4\x85pi\xc5\x82 b\xc5\x82\xc4\x85d podczas logowania: b\xc5\x82\xc4\x85d POST', True)

    def test_login_verification_correct_data(self):
        client = Client()
        response = client.post(
            '/login/verify/', {'login': valid_username, 'password': valid_user_password})
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/all/')
        self.assertIs(client.session.get('logged_in_as')
                      == valid_username, True)

    def test_login_verification_wrong_password(self):
        client = Client()
        response = client.post(
            '/login/verify/', {'login': valid_username, 'password': wrong_user_password})
        self.assertEquals(response.status_code, 302)
        self.assertIs(client.session.get('logged_in_as'), None)

    def test_login_verification_wrong_login(self):
        client = Client()
        response = client.post(
            '/login/verify/', {'login': wrong_username, 'password': valid_user_password})
        self.assertEquals(response.status_code, 302)
        self.assertIs(client.session.get('logged_in_as'), None)

    def test_login_verification_with_missing_login(self):
        client = Client()
        response = client.post(
            '/login/verify/', {'password': valid_user_password})
        self.assertEquals(response.status_code, 200)
        self.assertIs(response.content ==
                      b'Wyst\xc4\x85pi\xc5\x82 b\xc5\x82\xc4\x85d podczas logowania: b\xc5\x82\xc4\x85d POST', True)

    def test_login_verification_with_missing_password(self):
        client = Client()
        response = client.post('/login/verify/', {'login': valid_email})
        self.assertEquals(response.status_code, 200)
        self.assertIs(response.content ==
                      b'Wyst\xc4\x85pi\xc5\x82 b\xc5\x82\xc4\x85d podczas logowania: b\xc5\x82\xc4\x85d POST', True)


class LogoutViewTests(TestCase):
    @classmethod
    def setUpTestData(self):
        generate()

    def test_logout_after_login(self):
        client = Client()
        client.post('/login/verify/',
                    {'login': valid_username, 'password': valid_user_password})
        response = client.get('/login/logout/')
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/all/')
        self.assertIs(client.session.get('logged_in_as'), None)

    def test_logout_with_no_login(self):
        client = Client()
        response = client.get('/login/logout/')
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/all/')
        self.assertIs(client.session.get('logged_in_as'), None)
