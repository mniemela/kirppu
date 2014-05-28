from django.test import TestCase
from django.test.client import Client


class TestVendorLogin(TestCase):

    fixtures = ['kirppu/app/fixtures/vendor-test-data.json']

    def test_successful_login(self):
        """Should be able to login with correct credentials."""
        self.client = Client(enforce_csrf_checks=True)

        response = self.client.get('/kirppu/vendor/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_login.html')

        response = self.client.post('/kirppu/vendor/login/', {
            'csrfmiddlewaretoken':
                self.client.cookies['csrftoken'].value,
            'username': 'pelle',
            'password': '1234',
            'next': '/kirppu/vendor/'
        })
        self.assertRedirects(response, '/kirppu/vendor/')

    def test_no_username(self):
        """Login without username should show the login page again."""
        response = self.client.post(
            '/kirppu/vendor/login/',
            data = {
                'username': '',
                'password': '1234',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_login.html')

    def test_no_password(self):
        """Login without passoword should show the login page again."""
        response = self.client.post(
            '/kirppu/vendor/login/',
            data = {
                'username': 'pelle',
                'password': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_login.html')

    def test_invalid_password(self):
        """Login with invalid password should show the login page again."""
        response = self.client.post(
            '/kirppu/vendor/login/',
            data = {
                'username': 'pelle',
                'password': 'blablabla',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_login.html')

    def test_not_a_vendor(self):
        """Should not be able to login with a user that is not vendor."""
        response = self.client.post(
            '/kirppu/vendor/login/',
            data = {
                'username': 'pate',
                'password': 'abcd',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_login.html')
