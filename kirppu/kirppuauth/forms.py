from django import forms
from django.contrib.auth import get_user_model
from django.core import validators
from django.conf import settings
from kirppu.app.models import Clerk
from kompassi_crowd.kompassi_client import kompassi_get, KompassiError, user_defaults_from_kompassi
import re

__author__ = 'jyrkila'


class ClerkAddForm(forms.Form):
    username = forms.CharField(max_length=30,
        validators=[validators.RegexValidator(re.compile('^[\w.@+-]+$'), 'Enter a valid username.',
                                      'invalid')]
    )

    def save(self):
        username = self.cleaned_data["username"]
        user = get_user_model().objects.filter(username=username)
        if len(user) > 0:
            user = user[0]

            if user.is_clerk():
                return user.clerk, False
        else:
            user = None

        if user is None:
            if 'kompassi_crowd.backends.KompassiCrowdAuthenticationBackend' in settings.AUTHENTICATION_BACKENDS:
                user = self.save_crowd(username)
            else:
                user = get_user_model()(username=username)
                user.save()

        clerk = Clerk(user=user)
        clerk.save()
        return clerk, True

    @staticmethod
    def save_crowd(username):
        try:
            kompassi_user = kompassi_get('people', username)
        except KompassiError as e:
            raise KompassiError(u'failed to get kompassi user {username}: {e}'.format(username=username, e=e))

        user, created = get_user_model().objects.get_or_create(
            username=username,
            defaults=user_defaults_from_kompassi(kompassi_user)
        )
        return user
