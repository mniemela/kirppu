from django.conf.urls import url, patterns
from .api import AJAX_FUNCTIONS

__author__ = 'jyrkila'

_urls = [url('^checkout.js$', 'checkout_js', name='checkout_js')]
_urls.extend([
    url(func.url, func.name, name=func.view_name)
    for func in AJAX_FUNCTIONS.itervalues()
])

urlpatterns = patterns('kirppu.app.checkout.api', *_urls)
