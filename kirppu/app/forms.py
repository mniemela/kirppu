from django import forms
from django.contrib.auth.forms import AuthenticationForm

from kirppu.app.models import Vendor
from kirppu.kirppuauth.models import User
from kirppu.kirppuauth.admin import KirppuUserCreationForm

class VendorAuthenticationForm(AuthenticationForm):

    def clean(self):
        ret = super(VendorAuthenticationForm, self).clean()

        # Check that the user is registered as a vendor.
        user = self.get_user()
        if user and not user.is_vendor():
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
                params={'username': self.username_field.verbose_name},
            )

        return ret


class VendorCreationForm(KirppuUserCreationForm):

    def save(self):
        user = super(VendorCreationForm, self).save(commit=False)
        user.save()
        Vendor.objects.create(user=user)
        return user
