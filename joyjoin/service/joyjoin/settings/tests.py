import re

from django.test import Client, TestCase
from django.http import HttpRequest
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages import get_messages

from .views import complete
from common.generate_test_data import generate
from login.tests import login_client_for_tests

correctData = {'name': 'Stanislaw',
               'email': 'stachu@wp.pl',
               'password': 'konstantynopol',
               'password_2': 'konstantynopol',
               'description': '',
               'birth_date': '1998-01-01'
               }


class SettingsViewTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_settings_view(self):
        client = Client()
        client.post('/login/verify/',
                    {'login': 'monika', 'password': 'monika'})
        response = client.get('/settings/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Ustawienia użytkownika')
        self.assertContains(response, 'ZAPISZ')

    def test_settings_view_without_login(self):
        client = Client()
        response = client.get('/settings/')
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/login/')


class VerifyViewTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_complete_on_correct_data(self):
        client = Client()
        client.post('/login/verify/',
                    {'login': 'monika', 'password': 'monika'})
        response = client.post('/settings/complete/', correctData)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/settings/')

    def test_complete_on_correct_data_with_follow(self):
        client = Client()
        client.post('/login/verify/',
                    {'login': 'monika', 'password': 'monika'})
        response = client.post('/settings/complete/', correctData, follow=True)
        self.assertEquals(response.status_code, 200)
        for msg in response.context['messages']:
            self.assertEquals(
                msg.message, 'Dane użytkownika zostały poprawione')

    def test_complete_on_incorrect_data(self):
        client = Client()
        incorrectData = correctData.copy()
        incorrectData['password_2'] = 'bizancjum'
        client.post('/login/verify/',
                    {'login': 'monika', 'password': 'monika'})
        response = client.post('/settings/complete/', incorrectData)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/settings/')

    def test_complete_on_incorrect_data_with_follow(self):
        client = Client()
        incorrectData = correctData.copy()
        incorrectData['password_2'] = 'bizancjum'
        client.post('/login/verify/',
                    {'login': 'monika', 'password': 'monika'})
        response = client.post('/settings/complete/',
                               incorrectData, follow=True)
        self.assertEquals(response.status_code, 200)
        for msg in response.context['messages']:
            self.assertEquals(msg.message, 'Hasła nie są identyczne')

    def test_complete_without_login(self):
        client = Client()
        response = client.post('/settings/complete/', correctData)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response.url, '/login/')


class SettingsTests(TestCase):
    correctData = correctData

    @classmethod
    def setUp(cls):
        generate()

    def single_test(self, data, expectedResult):
        # utworzenie nowego zapytania
        request = HttpRequest()
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)
        request.POST = data
        request.session['logged_in_as'] = 'monika'

        # sprawdzenie poprawności danych
        complete(request)

        # wypisanie komunikatu w przypadku blednego zachowania funkcji
        for message in get_messages(request):
            assert message.extra_tags is expectedResult, message.extra_tags + \
                " " + str(request.POST)

    # Testy nazwiska
    def test_name_with_correct_data(self):
        data = self.correctData.copy()
        data['name'] = 'Jan Kowalski'
        self.single_test(data, 'OK')
        data['name'] = 'Andrzej Nowak'
        self.single_test(data, 'OK')
        data['name'] = 'xyz'
        self.single_test(data, 'OK')
        data['name'] = 'Miłosz'
        self.single_test(data, 'OK')
        data['name'] = 'Konstantypolitańczykowianeczka czy jakoś tak'
        self.single_test(data, 'OK')
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
        data['password'] = data['password_2'] = 'eluwinax'
        self.single_test(data, 'OK')
        data['password'] = data['password_2'] = 'sdnfsdnfksjdn!@!#!$1235646589'
        self.single_test(data, 'OK')
        data['password'] = data['password_2'] = 'xddddddddddddddddd'
        self.single_test(data, 'OK')
        data['password'] = data['password_2'] = '!!!!!!!!!!!!!!!'
        self.single_test(data, 'OK')
        data['password'] = data['password_2'] = 'asdfghjkl123123123'
        self.single_test(data, 'OK')
        data['password'] = data['password_2'] = ''
        self.single_test(data, 'OK')

    def test_password_with_too_short_password(self):
        data = self.correctData.copy()
        data['password'] = data['password_2'] = 'eluwina'
        self.single_test(data, 'password_too_short')
        data['password'] = data['password_2'] = 'unodos'
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
        data['birth_date'] = '1998-12-01'
        self.single_test(data, 'OK')
        data['birth_date'] = '1900-12-31'
        self.single_test(data, 'OK')
        data['birth_date'] = '2008-01-01'
        self.single_test(data, 'OK')
        data['birth_date'] = '2004-02-29'
        self.single_test(data, 'OK')
        data['birth_date'] = '1996-02-29'
        self.single_test(data, 'OK')
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

    # Testy opisu
    def test_description_too_long(self):
        data = self.correctData.copy()
        data['description'] = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, \
sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Tempor id eu nisl nunc mi. \
Volutpat sed cras ornare arcu. Quam id leo in vitae. Eget mi proin sed libero enim sed faucibus turpis. \
Dignissim convallis aenean et tortor at risus viverra. Vitae congue eu consequat ac felis donec et odio. \
Nunc mi ipsum faucibus vitae aliquet. Velit aliquet sagittis id consectetur purus ut faucibus. \
Et ultrices neque ornare aenean euismod. Morbi leo urnae."""
        self.single_test(data, 'description_too_long')


class SettingsPicUploadTests(TestCase):

    @classmethod
    def setUp(cls):
        generate()

    def test_picture_upload(self):
        client = Client()
        login_client_for_tests(client)
        response = client.get('/user/monika/')
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/default.jpg">')
        self.assertTrue(re_img_src.search(response.content))
        post_data = correctData.copy()
        test_pic = open('settings/test_data/perfect_square.png', 'rb+')
        post_data['image'] = test_pic
        response = client.post('/settings/complete/', post_data, follow=True)
        response = client.get('/user/monika/')
        self.assertEqual(response.status_code, 200)
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/monika.png">')
        self.assertTrue(re_img_src.search(response.content))

    def test_picture_upload_with_wrong_filetype(self):
        client = Client()
        login_client_for_tests(client)
        response = client.get('/user/monika/')
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/default.jpg">')
        self.assertTrue(re_img_src.search(response.content))
        post_data = correctData.copy()
        test_pic = open('settings/test_data/not_a_picture.png', 'rb+')
        post_data['image'] = test_pic
        response = client.post('/settings/complete/', post_data, follow=True)
        for msg in response.context['messages']:
            self.assertEquals(
                msg.message, 'Wybrano zły typ pliku')
        response = client.get('/user/monika/')
        self.assertEqual(response.status_code, 200)
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/monika.png">')
        self.assertFalse(re_img_src.search(response.content))

    def test_picture_upload_with_landscape_picture(self):
        client = Client()
        login_client_for_tests(client)
        response = client.get('/user/monika/')
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/default.jpg">')
        self.assertTrue(re_img_src.search(response.content))
        post_data = correctData.copy()
        test_pic = open('settings/test_data/landscape.png', 'rb+')
        post_data['image'] = test_pic
        response = client.post('/settings/complete/', post_data, follow=True)
        response = client.get('/user/monika/')
        self.assertEqual(response.status_code, 200)
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/monika.png">')
        self.assertTrue(re_img_src.search(response.content))

    def test_picture_upload_with_portrait_picture(self):
        client = Client()
        login_client_for_tests(client)
        response = client.get('/user/monika/')
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/default.jpg">')
        self.assertTrue(re_img_src.search(response.content))
        post_data = correctData.copy()
        test_pic = open('settings/test_data/portrait.png', 'rb+')
        post_data['image'] = test_pic
        response = client.post('/settings/complete/', post_data, follow=True)
        response = client.get('/user/monika/')
        self.assertEqual(response.status_code, 200)
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/monika.png">')
        self.assertTrue(re_img_src.search(response.content))

    def test_picture_upload_with_jpeg_picture(self):
        client = Client()
        login_client_for_tests(client)
        response = client.get('/user/monika/')
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/default.jpg">')
        self.assertTrue(re_img_src.search(response.content))
        post_data = correctData.copy()
        test_pic = open('settings/test_data/perfect_square.jpg', 'rb+')
        post_data['image'] = test_pic
        response = client.post('/settings/complete/', post_data, follow=True)
        response = client.get('/user/monika/')
        self.assertEqual(response.status_code, 200)
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/monika.jpg">')
        self.assertTrue(re_img_src.search(response.content))

    def test_picture_reupload(self):
        client = Client()
        login_client_for_tests(client)
        response = client.get('/user/monika/')
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/default.jpg">')
        self.assertTrue(re_img_src.search(response.content))
        post_data = correctData.copy()
        test_pic = open('settings/test_data/perfect_square.png', 'rb+')
        post_data['image'] = test_pic
        response = client.post('/settings/complete/', post_data, follow=True)
        response = client.get('/user/monika/')
        self.assertEqual(response.status_code, 200)
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/monika.png">')
        self.assertTrue(re_img_src.search(response.content))
        test_pic = open('settings/test_data/perfect_square.png', 'rb+')
        post_data['image'] = test_pic
        response = client.post('/settings/complete/', post_data, follow=True)
        response = client.get('/user/monika/')
        self.assertEqual(response.status_code, 200)
        re_img_src = re.compile(b'<img class="avatar" alt=".+" src="/media/monika.png">')
        self.assertTrue(re_img_src.search(response.content))
