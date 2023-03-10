from django.test import Client, TestCase

from common.generate_test_data import generate, user_prototypes


valid_nonexistent_user_login = 'susskind'
valid_user_login = 'monika'


class UserViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        generate()

    def test_user_view_for_nonexistent_user(self):
        client = Client()
        response = client.get('/user/' + valid_nonexistent_user_login + '/')
        self.assertEqual(response.status_code, 404)

    def test_user_view(self):
        client = Client()
        response = client.get('/user/' + valid_user_login + '/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Data dołączenia')
        self.assertContains(response, 'Login: </b> ' + valid_user_login)
        user_prototype_index = 1
        description_index_in_user_prototype = 2
        test_user_description = user_prototypes[user_prototype_index][description_index_in_user_prototype]
        self.assertNotEqual(test_user_description, '')
        self.assertContains(response, test_user_description)
