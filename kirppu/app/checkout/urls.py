from django.conf.urls import url, patterns

__author__ = 'jyrkila'

urlpatterns = patterns('kirppu.app.checkout.api',
    url(r'^validate_counter', 'validate_counter', name='api_validate_counter'),
    url(r'^clerk/login$', 'login_clerk', name='api_clerk_login'),
    url(r'^clerk/logout$', 'logout_clerk', name='api_clerk_logout'),
    url(r'^item/info$', 'get_item', name='api_item_info'),
    url(r'^item/reserve$', 'reserve_item_for_receipt', name='api_item_reserve'),
    # url(r'^item/release$', 'release_item_from_receipt'),
    url(r'^receipt/start$', 'start_receipt', name='api_receipt_start'),
    url(r'^receipt/finish$', 'finish_receipt', name='api_receipt_finish'),
)
