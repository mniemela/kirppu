from django.test import TestCase
from django.test.client import Client


class TestLogout(TestCase):

    fixtures = ['kirppu/app/fixtures/vendor-test-data.json']

    def test_vendor_loginout(self):
        """Should be able to logout after login."""
        self.client.post(
            '/kirppu/vendor/login/',
            {'username': 'pelle', 'password': '1234'},
        )
        self.assertIn('_auth_user_id', self.client.session)
        # logged in

        response = self.client.get('/kirppu/logout/')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_logged_out.html')
