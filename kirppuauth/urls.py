from django.conf.urls import patterns, include, url

urlpatterns = patterns('kirppuauth.views',
    url(r'^addclerk$', 'register_clerk', name='kirppu_register_clerk'),
)
