from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render
from kirppu.kirppuauth.forms import ClerkAddForm
from kirppu.util import get_form

__author__ = 'jyrkila'


@login_required
def register_clerk(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Forbidden")

    form = get_form(ClerkAddForm, request)
    if request.method == "POST" and form.is_valid():
        clerk, created = form.save()
        if created:
            messages.info(request, "User {0} created as Clerk.".format(clerk))
        else:
            messages.warning(request, "User {0} was already a Clerk.".format(clerk))
        return HttpResponseRedirect(reverse("kirppuauth:kirppu_register_clerk"))

    return render(request, "kirppuauth_clerk_register.html", {
        'form': form,
    })
