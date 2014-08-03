from django import forms
from django.contrib import admin
from django.utils.translation import ugettext
from django.contrib import messages
from kirppu.app.forms import ClerkGenerationForm

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


# noinspection PyMethodMayBeStatic
class ClerkAdmin(admin.ModelAdmin):
    actions = ["_gen_clerk_code", "_del_clerk_code", "_move_clerk_code"]
    list_display = ('id', 'user', 'access_key')
    ordering = ('user__first_name', 'user__last_name')
    search_fields = ['user__first_name', 'user__last_name', 'user__username']

    def _gen_clerk_code(self, request, queryset):
        for clerk in queryset:
            if clerk.access_key is None:
                clerk.generate_access_key()
                clerk.save(update_fields=["access_key"])
    _gen_clerk_code.short_description = ugettext(u"Generate missing Clerk access codes")

    def _del_clerk_code(self, request, queryset):
        queryset.update(access_key=None)
    _del_clerk_code.short_description = ugettext(u"Delete Clerk access codes")

    def _move_error(self, request):
        self.message_user(request,
                          ugettext(u"Must select exactly one 'unbound' and one 'bound' Clerk for this operation"),
                          messages.ERROR)

    def _move_clerk_code(self, request, queryset):
        if len(queryset) != 2:
            self._move_error(request)
            return

        # Guess the order.
        unbound = queryset[0]
        bound = queryset[1]
        if queryset[1].user is None:
            # Was wrong, swap around.
            bound, unbound = unbound, bound

        if unbound.user is not None or bound.user is None:
            # Selected wrong rows.
            self._move_error(request)
            return

        # Assign the new code to be used. Remove the unbound item first, so unique-check doesn't break.
        bound.access_key = unbound.access_key
        unbound.delete()
        bound.save(update_fields=["access_key"])
        self.message_user(request, ugettext(u"Access code set for '{0}'").format(bound.user))
    _move_clerk_code.short_description = ugettext(u"Move unused access code to existing Clerk.")

    def get_form(self, request, obj=None, **kwargs):
        if "unbound" in request.GET:
            # Custom form for creating multiple Clerks at same time.
            return ClerkGenerationForm
        return super(ClerkAdmin, self).get_form(request, obj, **kwargs)

    def save_related(self, request, form, formsets, change):
        if isinstance(form, ClerkGenerationForm):
            # No related fields...
            return
        return super(ClerkAdmin, self).save_related(request, form, formsets, change)

    def log_addition(self, request, object):
        if isinstance(object, ClerkGenerationForm):
            # Log all added items separately.
            for item in object.saved_list:
                super(ClerkAdmin, self).log_addition(request, item)
            return
        super(ClerkAdmin, self).log_addition(request, object)


admin.site.register(Clerk, ClerkAdmin)
