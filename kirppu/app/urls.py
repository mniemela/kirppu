from django.conf.urls import patterns, url

__author__ = 'jyrkila'

urlpatterns = patterns('kirppu.app.views',
    url(r'^page/(?P<sid>\d+)/(?P<eid>\d+)', 'get_items', name='page'),
    url(r'^code/(?P<iid>\w+?)\.(?P<ext>\w+)', 'get_item_image', name='image'),
    url(r'^commands/(?P<eid>\d+)', 'get_commands', name='commands'),
    url(r'^command/(?P<iid>\w+?)\.(?P<ext>\w+)', 'get_command_image', name='command_image'),
    url(r'^checkout/(?P<eid>\d+)', 'checkout_view'),
)
