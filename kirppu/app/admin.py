from django import forms
from django.contrib import admin
from django.utils.translation import ugettext

from kirppu.app.models import Clerk, Item, Vendor

__author__ = 'jyrkila'


def _gen_ean(modeladmin, request, queryset):
    for item in queryset:
        if item.code is None or len(item.code) == 0:
            item.code = item.gen_barcode()
            item.save(update_fields=["code"])
_gen_ean.short_description = ugettext(u"Generate bar codes for items missing it")


def _del_ean(modeladmin, request, queryset):
    queryset.update(code="")
_del_ean.short_description = ugettext(u"Delete generated bar codes")


def _regen_ean(modeladmin, request, queryset):
    _del_ean(modeladmin, request, queryset)
    _gen_ean(modeladmin, request, queryset)
_regen_ean.short_description = ugettext(u"Re-generate bar codes for items")


class ItemAdmin(admin.ModelAdmin):
    actions = [_gen_ean, _del_ean, _regen_ean]
    list_display = ('name', 'code', 'price', 'state', 'vendor')
    ordering = ('vendor', 'name')
    search_fields = ['name', 'code']
admin.site.register(Item, ItemAdmin)


class VendorAdmin(admin.ModelAdmin):
    ordering = ('user__first_name', 'user__last_name')
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
admin.site.register(Vendor, VendorAdmin)


class ClerkAdmin(admin.ModelAdmin):
    ordering = ('user__first_name', 'user__last_name')
    search_fields = ['user__first_name', 'user__last_name', 'user__username']
admin.site.register(Clerk, ClerkAdmin)
