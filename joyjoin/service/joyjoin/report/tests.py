from django.test import TestCase, Client
from report.models import Report, ReportCategory
from common.models import User
from django.forms import ValidationError
from common.generate_test_data import generate
from login.tests import login_client_for_tests


class ReportModelStrMethodTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()

    def test_report_category_str_method(self):
        obj = ReportCategory.objects.first()
        self.assertTrue(str(obj))

    def test_report_str_method(self):
        report = Report.objects.filter(user__isnull=True).first()
        self.assertTrue(str(report))
        report = Report.objects.filter(user__isnull=False).first()
        self.assertTrue(str(report))


class ReportCategoryModelTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()
        # przykładowa kategoria
        cls.category_name = 'Testowa kategoria'
        cls.category = ReportCategory(name=cls.category_name)

    def test_add_new_category(self):
        self.assertFalse(ReportCategory.objects.filter(
            name=self.category_name).exists())
        self.category.save()
        self.assertTrue(ReportCategory.objects.filter(
            name=self.category_name).exists())

    def test_add_new_category_with_no_name(self):
        self.category.name = None
        count_before_save = ReportCategory.objects.all().count()
        with self.assertRaises(ValidationError):
            self.category.save()
        count_after_save = ReportCategory.objects.all().count()
        self.assertEquals(count_before_save, count_after_save)

    def test_add_new_category_with_blank_name(self):
        self.category.name = ''
        count_before_save = ReportCategory.objects.all().count()
        with self.assertRaises(ValidationError):
            self.category.save()
        count_after_save = ReportCategory.objects.all().count()
        self.assertEquals(count_before_save, count_after_save)


class ReportModelTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()
        # przykładowe zgłoszenie z autorem
        cls.category_name = 'Testowa kategoria'
        cls.category = ReportCategory(name=cls.category_name)
        cls.category.save()
        cls.text = 'Przykładowy tekst'
        cls.user = User.objects.all().first()
        cls.report = Report(
            text=cls.text, category=cls.category, user=cls.user)

    def test_add_new_report(self):
        self.assertFalse(Report.objects.filter(text=self.text).exists())
        self.report.save()
        self.assertTrue(Report.objects.filter(text=self.text).exists())

    def test_add_new_report_with_no_user(self):
        self.report.user = None
        self.assertFalse(Report.objects.filter(text=self.text).exists())
        self.report.save()
        self.assertTrue(Report.objects.filter(text=self.text).exists())

    def test_add_new_report_with_no_text(self):
        self.report.text = None
        count_before_save = Report.objects.all().count()
        with self.assertRaises(ValidationError):
            self.report.save()
        count_after_save = Report.objects.all().count()
        self.assertEquals(count_before_save, count_after_save)

    def test_add_new_report_with_blank_text(self):
        self.report.text = ''
        count_before_save = Report.objects.all().count()
        with self.assertRaises(ValidationError):
            self.report.save()
        count_after_save = Report.objects.all().count()
        self.assertEquals(count_before_save, count_after_save)

    def test_add_new_report_with_no_category(self):
        self.report.category = None
        count_before_save = Report.objects.all().count()
        with self.assertRaises(ValidationError):
            self.report.save()
        count_after_save = Report.objects.all().count()
        self.assertEquals(count_before_save, count_after_save)


class ReportViewTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()
        # przykładowe zgłoszenie bez autora
        cls.category_name = 'Testowa kategoria'
        cls.category = ReportCategory(name=cls.category_name)
        cls.category.save()
        cls.text = 'Przykładowy tekst'
        cls.report = Report(text=cls.text, category=cls.category)
        # niezależne zgłoszenie z autorem
        cls.independent_report = Report.objects.filter(
            user__login='norbert').first()

    def test_report_view_show_reports_right_and_logged_in(self):
        client = Client()
        login_client_for_tests(client)
        self.report.user = User.objects.get(
            login=client.session.get('logged_in_as'))
        self.report.save()

        response = client.get('/report/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, self.text)
        self.assertNotContains(response, self.independent_report.text)
        self.assertContains(response, 'Twoje zgloszenia')

    def test_report_view_show_reports_right_and_not_logged_in(self):
        client = Client()
        self.report.save()

        response = client.get('/report/')
        self.assertEquals(response.status_code, 200)
        self.assertNotContains(response, self.text)
        self.assertNotContains(response, self.independent_report.text)
        self.assertNotContains(response, 'Twoje zgloszenia')


class AddViewTests(TestCase):
    @classmethod
    def setUp(cls):
        generate()
        # klient
        cls.client = Client()
        # dane zgłoszenia
        cls.category_name = 'Testowa kategoria'
        cls.category = ReportCategory(name=cls.category_name)
        cls.category.save()
        cls.text = 'Przykładowy tekst'

    def test_add_view(self):
        login_client_for_tests(self.client)
        self.assertFalse(Report.objects.filter(text=self.text).exists())
        response = self.client.post(
            '/report/add/', {'text': self.text, 'category': self.category_name})
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Report.objects.filter(text=self.text).exists())

    def test_add_view_with_no_text(self):
        login_client_for_tests(self.client)
        count_before_save = Report.objects.all().count()
        response = self.client.post(
            '/report/add/', {'category': self.category_name})
        self.assertEquals(response.status_code, 400)
        count_after_save = Report.objects.all().count()
        self.assertEquals(count_before_save, count_after_save)

    def test_add_view_with_blank_text(self):
        self.text = ''
        login_client_for_tests(self.client)
        count_before_save = Report.objects.all().count()
        response = self.client.post(
            '/report/add/', {'text': self.text, 'category': self.category_name})
        self.assertEquals(response.status_code, 400)
        count_after_save = Report.objects.all().count()
        self.assertEquals(count_before_save, count_after_save)

    def test_add_view_with_no_category(self):
        login_client_for_tests(self.client)
        self.assertFalse(Report.objects.filter(text=self.text).exists())
        response = self.client.post('/report/add/', {'text': self.text})
        self.assertEquals(response.status_code, 400)
        self.assertFalse(Report.objects.filter(text=self.text).exists())

    def test_add_view_with_undefined_category(self):
        login_client_for_tests(self.client)
        self.assertFalse(Report.objects.filter(text=self.text).exists())
        response = self.client.post(
            '/report/add/', {'text': self.text, 'category': 'nie ma takiej'})
        self.assertEquals(response.status_code, 404)
        self.assertFalse(Report.objects.filter(text=self.text).exists())

    # niezalogowani

    def test_add_view_and_not_logged_in(self):
        self.assertFalse(Report.objects.filter(text=self.text).exists())
        response = self.client.post(
            '/report/add/', {'text': self.text, 'category': self.category_name})
        self.assertEquals(response.status_code, 302)
        self.assertTrue(Report.objects.filter(text=self.text).exists())

    def test_add_view_with_no_text_and_not_logged_in(self):
        count_before_save = Report.objects.all().count()
        response = self.client.post(
            '/report/add/', {'category': self.category_name})
        self.assertEquals(response.status_code, 400)
        count_after_save = Report.objects.all().count()
        self.assertEquals(count_before_save, count_after_save)

    def test_add_view_with_blank_text_and_not_logged_in(self):
        self.text = ''
        count_before_save = Report.objects.all().count()
        response = self.client.post(
            '/report/add/', {'text': self.text, 'category': self.category_name})
        self.assertEquals(response.status_code, 400)
        count_after_save = Report.objects.all().count()
        self.assertEquals(count_before_save, count_after_save)

    def test_add_view_with_no_category_and_not_logged_in(self):
        self.assertFalse(Report.objects.filter(text=self.text).exists())
        response = self.client.post('/report/add/', {'text': self.text})
        self.assertEquals(response.status_code, 400)
        self.assertFalse(Report.objects.filter(text=self.text).exists())

    def test_add_view_with_undefined_category_and_not_logged_in(self):
        self.assertFalse(Report.objects.filter(text=self.text).exists())
        response = self.client.post(
            '/report/add/', {'text': self.text, 'category': 'nie ma takiej'})
        self.assertEquals(response.status_code, 404)
        self.assertFalse(Report.objects.filter(text=self.text).exists())
