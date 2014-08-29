from django.conf import settings
from django.conf.urls import url, patterns
from .api import AJAX_FUNCTIONS

__author__ = 'jyrkila'

if settings.KIRPPU_CHECKOUT_ACTIVE:
    # Only activate API when checkout is active.

    _urls = [url('^checkout.js$', 'checkout_js', name='checkout_js')]
    _urls.extend([
        url(func.url, func.name, name=func.view_name)
        for func in AJAX_FUNCTIONS.itervalues()
    ])

else:
    _urls = []

urlpatterns = patterns('kirppu.app.checkout.api', *_urls)
