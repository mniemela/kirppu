# encoding: utf-8

from django.test import TestCase
from django.test.client import Client
import os.path


class TestVendorSignup(TestCase):
    fixtures = map(os.path.normpath,
            ['kirppu/app/fixtures/vendor-test-data.json'])

    def try_signup(self, user, pass1, pass2=None):
        params = {
            'username': user,
            'password1': pass1,
            'password2': pass1 if pass2 is None else pass2,
        }
        return self.client.post('/kirppu/vendor/signup/', params)

    def assert_login(self, username, password, success_expected=True):
        """Attempt login and check that it fails/succeeds as expected."""
        # logout first
        self.client.get('/kirppu/logout/')
        self.assertNotIn('_auth_user_id', self.client.session)

        response = self.client.post(
            '/kirppu/vendor/login/',
            {'username': username, 'password': password},
        )
        if success_expected:
            self.assertIn(
                '_auth_user_id', self.client.session,
                u'Could not login user "{0}" with password "{1}"'
                u''.format(username, password)
            )
        else:
            self.assertNotIn(
                '_auth_user_id', self.client.session,
                u'Unexpectedly able to login user "{0}" with password "{1}"'
                u''.format(username, password)
            )

    def test_successful_signup(self):
        """Should be able to sign up and then log in."""
        # sign up
        response = self.try_signup('maija', u'sälä合言葉sänä')
        self.assertRedirects(response, '/kirppu/vendor/')
        self.assertIn('_auth_user_id', self.client.session)

        self.assert_login('maija', u'sälä合言葉sänä')

    def test_duplicate_username(self):
        """Should not be able to sign up with an existing username."""
        # Test with a User who is not a vendor.
        response = self.try_signup('pate', 'salasana')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_signup.html')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assert_login('pate', 'salasana', False)

        # Test with a User who is a vendor.
        response = self.try_signup('pelle', '1234')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_vendor_signup.html')
        self.assertNotIn('_auth_user_id', self.client.session)
