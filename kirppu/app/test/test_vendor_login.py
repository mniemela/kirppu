from django.test import TestCase
from django.test.client import Client
import os.path


class TestVendorLogin(TestCase):
    fixtures = map(os.path.normpath,
            ['kirppu/app/fixtures/vendor-test-data.json'])

    def try_login(self, username, password, rest=None):
        params = {
            'username': username,
            'password': password,
        }
        if rest is not None:
            params.update(rest)

        return self.client.post(
            '/kirppu/vendor/login/',
            params,
        )


    def test_successful_login(self):
        """Should be able to login with correct credentials."""
        self.client = Client(enforce_csrf_checks=True)

        response = self.client.get('/kirppu/vendor/login/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_login.html')

        response = self.try_login(
            'pelle', '1234',
            {'csrfmiddlewaretoken': self.client.cookies['csrftoken'].value,
             'next': '/'},
        )
        self.assertRedirects(response, '/')
        self.assertIn('_auth_user_id', self.client.session)

    def test_missing_csrf_token(self):
        """Missing CSRF token should display a warning."""
        self.client = Client(enforce_csrf_checks=True)
        response = self.try_login('pelle', '1234')
        self.assertEqual(response.status_code, 403)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_no_username(self):
        """Login without username should show the login page again."""
        response = self.try_login('', '1234')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_login.html')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_no_password(self):
        """Login without passoword should show the login page again."""
        response = self.try_login('pelle', '')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_login.html')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_password(self):
        """Login with invalid password should show the login page again."""
        response = self.try_login('pelle', 'blablabla')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_login.html')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_not_a_vendor(self):
        """Should not be able to login with a user that is not vendor."""
        response = self.try_login('pate', 'abcd')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_login.html')
        self.assertNotIn('_auth_user_id', self.client.session)
