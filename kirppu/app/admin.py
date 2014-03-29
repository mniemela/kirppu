from django import forms
from django.contrib import admin
from django.utils.translation import ugettext
from kirppu.app.models import Event, Item, Seller, EventCleric

__author__ = 'jyrkila'


class EventAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'start_date', 'end_date')
    ordering = ('name',)
admin.site.register(Event, EventAdmin)


def _gen_ean(modeladmin, request, queryset):
    for item in queryset:
        if item.code is None or len(item.code) == 0:
            new_code = item.gen_barcode()
            item.code = new_code
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
    list_display = ('name', 'code', 'price', 'state', 'seller')
    ordering = ('seller', 'name')
    search_fields = ['name', 'code']
admin.site.register(Item, ItemAdmin)


class SellerForm(forms.ModelForm):
    def save(self, commit=True):
        self.instance.index = self.instance.event.get_next_index()
        return super(SellerForm, self).save(commit)

    #noinspection PyClassHasNoInit
    class Meta:
        model = Seller
        exclude = ['index']


class SellerAdmin(admin.ModelAdmin):
    form = SellerForm
    list_display = ('__unicode__', 'event', 'index', 'pk')
    ordering = ('event', 'user__first_name', 'user__last_name')
    search_fields = ['user__first_name', 'user__last_name', 'user__username']

admin.site.register(Seller, SellerAdmin)


def _regen_cleric_code(modeladmin, request, queryset):
    for row in queryset:
        row.code = ""
        row.save()
_regen_cleric_code.short_description = ugettext(u"Re-generate cleric codes")


class ClericForm(forms.ModelForm):
    code = forms.CharField(required=False)

    #noinspection PyClassHasNoInit
    class Meta:
        model = EventCleric


class ClericAdmin(admin.ModelAdmin):
    form = ClericForm
    actions = [_regen_cleric_code]
    list_display = ('event', 'user', 'code')

admin.site.register(EventCleric, ClericAdmin)
