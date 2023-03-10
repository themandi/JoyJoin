from django.test import Client, TestCase


class AllViewTests(TestCase):
    def test_all_view(self):
        client = Client()
        response = client.get('/all/')
        self.assertEquals(response.status_code, 200)
        self.assertIs(response.context['this_is_the_all_view'], True)
        self.assertIs(response.context['this_is_section_view'], True)
        self.assertEquals(response.context['section_name'], 'all')


class RulesViewTests(TestCase):
    def test_rules_view(self):
        client = Client()
        response = client.get('/rules/')
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Regulamin')
        self.assertContains(response, 'Pisz zwięźle i na temat')
