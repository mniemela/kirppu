from django.conf.urls import patterns, include, url

urlpatterns = patterns('kirppu.kirppuauth.views',
    url(r'^addclerk$', 'register_clerk', name='kirppu_register_clerk'),
)
