from django import forms

from kirppu.app.models import Clerk, ReceiptItem
from kirppu.app.utils import StaticText


class ClerkGenerationForm(forms.ModelForm):
    count = forms.IntegerField(
        min_value=0,
        initial=1,
        help_text=u"Count of empty Clerks to generate")

    def __init__(self, *args, **kwargs):
        super(ClerkGenerationForm, self).__init__(*args, **kwargs)
        self._save_list = None
        self._saved_list = None

    def generate(self, commit=True):
        return Clerk.generate_empty_clerks(self.cleaned_data["count"], commit=commit)

    def save(self, commit=True):
        # Save-hack... Admin calls this first with commit=False and then commit=True,
        # so store the list of items at first time to variable, and do the real saving
        # when the commit is True.
        if self._save_list is not None:
            if commit:
                for item in self._save_list:
                    item.save()
                self._saved_list = self._save_list
                self._save_list = None
            return self

        if commit:
            # Called directly commit=True, so do so.
            self._saved_list = self.generate(commit=True)
            return self

        else:
            self._save_list = self.generate(commit=False)
            # Admin expects to find verbose_name from Meta, which does not exist in
            # ModelFormOptions, so add kind of own name there.
            if "verbose_name" not in dir(self._meta):
                self._meta.verbose_name = "ClerkGeneration"
            return self

    # noinspection PyMethodMayBeStatic
    def _get_pk_val(self):
        # (Save-hack)
        return 0

    def __unicode__(self):
        # (Save-hack) When form is valid, this is used in the "Created x" -message.
        if self.is_valid():
            return u"{0} of Clerk(s)".format(self.cleaned_data["count"])

        return "ClerkGenerationForm"

    @property
    def saved_list(self):
        return self._saved_list

    class Meta:
        model = Clerk
        fields = ("count",)


class ReceiptItemAdminForm(forms.ModelForm):
    price = StaticText(
        label=u"Price",
        text=u"--",
    )

    def __init__(self, *args, **kwargs):
        super(ReceiptItemAdminForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs:
            mdl = kwargs["instance"]
            self.fields["price"].widget.set_text(mdl.item.price)

    class Meta:
        model = ReceiptItem


class ReceiptAdminForm(forms.ModelForm):
    start_time = StaticText(
        label=u"Start time",
        text=u"--"
    )

    def __init__(self, *args, **kwargs):
        super(ReceiptAdminForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs:
            mdl = kwargs["instance"]
            self.fields["start_time"].widget.set_text(mdl.start_time)
