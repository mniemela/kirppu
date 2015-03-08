from django import template
from django.conf import settings
from django.core.urlresolvers import reverse

register = template.Library()

__author__ = 'codez'


@register.simple_tag(name="kirppu_login_url")
def login_url():
    if settings.KIRPPU_USE_SSO:
        return reverse("kirppu:login_view")
    return settings.LOGIN_URL


@register.simple_tag(name="kirppu_logout_url")
def logout_url():
    if settings.KIRPPU_USE_SSO:
        return reverse("kirppu:logout_view")
    return settings.LOGOUT_URL
