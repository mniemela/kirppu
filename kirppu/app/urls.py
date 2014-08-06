from django.conf.urls import patterns, url

__author__ = 'jyrkila'

urlpatterns = patterns('kirppu.app.views',
    url(r'^page/(?P<vendor_id>\d+)$', 'get_items', name='page'),
    url(r'^code/(?P<item_id>\w+?)\.(?P<ext>\w+)$',
        'get_item_barcode', name='item_barcode'),
    url(r'^commands/$', 'get_commands', name='commands'),
    url(r'^command/(?P<data>\w+?)\.(?P<ext>\w+)$',
        'get_barcode', name='command_barcode'),
    url(r'^barcode/(?P<data>\w+?)\.(?P<ext>\w+)$',
        'get_barcode', name='barcode'),
    url(r'^checkout/$', 'checkout_view'),
    url(r'^vendor/$', 'vendor_view', name='vendor_view'),
    url(r'^vendor/item/$', 'item_add', name='item_add'),
    url(r'^vendor/item/(?P<code>\w+?)/$', 'item_view', name='item_delete'),
    url(r'^vendor/item/(?P<code>\w+?)/price$', 'item_update_price', name='item_update_price'),
    url(r'^vendor/item/(?P<code>\w+?)/name$', 'item_update_name', name='item_update_name'),
    url(r'^vendor/item/(?P<code>\w+?)/type$', 'item_update_type', name='item_update_type'),
    url(r'^vendor/login/$', 'vendor_login', name='vendor_login'),
    url(r'^vendor/signup/$', 'vendor_signup', name='vendor_signup'),
    url(r'^logout/$', 'user_logout', name='user_logout'),
)
