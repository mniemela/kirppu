from django import forms
from django.contrib.auth.forms import AuthenticationForm

from kirppu.app.models import Vendor

class VendorAuthenticationForm(AuthenticationForm):

    def clean(self):
        ret = super(VendorAuthenticationForm, self).clean()

        # Check that the user is registered as a vendor.
        user = self.get_user()
        if user and user.vendor_set.count() == 0:
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name},
            )

        return ret
