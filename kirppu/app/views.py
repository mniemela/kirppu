from collections import namedtuple

import barcode
from barcode.writer import SVGWriter, ImageWriter

import django.contrib.auth as auth
import django.contrib.auth.views as auth_views
from django.core.context_processors import csrf
import django.core.urlresolvers as url
import django.forms as forms
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
)
from django.shortcuts import (
    get_object_or_404,
    render,
)
from django.utils.http import is_safe_url
from django.utils.translation import ugettext
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from kirppu.app.forms import (
    VendorAuthenticationForm,
    VendorCreationForm,
)
from kirppu.app.models import (
    Item,
    Clerk,
    CommandCode,
    Vendor,
)


def index(request):
    return HttpResponse("")


@require_http_methods(["POST"])
def item_update_price(request):
    str_price = request.POST.get("value", "0")
    str_price = str_price.replace(",", ".")
    
    try:
        cents = float(str_price) * 100 # price in cents
    except ValueError as __:
        cents = 0
    
    # Round up to nearest 50 cents.---
    if cents % 50 > 0:
        cents += 50 - cents % 50
    
    import time
    time.sleep(0.5)
    
    if cents == 0:
        return HttpResponseBadRequest("Na a!")
    
    str_euros = str(cents / 100.0)
    str_euros = str_euros.replace(".", ",")
    
    return HttpResponse(str_euros)


@require_http_methods(["POST"])
def item_update_name(request):
    name = request.POST.get("value", "no name")
    
    name = name[:80]
    
    import time
    time.sleep(0.5)
    
    return HttpResponse(name)


def get_items(request, vendor_id):
    """
    Get a page containing all items for vendor.

    :param request: HttpRequest object.
    :type request: django.http.request.HttpRequest
    :param vendor_id: Vendor ID
    :type vendor_id: str
    :return: HttpResponse or HttpResponseBadRequest
    """
    bar_type = request.GET.get("format", "svg").lower()
    tag_type = request.GET.get("tag", "short").lower()

    if bar_type not in ('svg', 'png'):
        return HttpResponseBadRequest(u"Image extension not supported")
    if tag_type not in ('short', 'long'):
        return HttpResponseBadRequest(u"Tag type not supported")

    try:
        vendor = Vendor.objects.get(id=vendor_id)
    except:
        return HttpResponseNotFound(u'Vendor not found.')

    items = Item.objects.filter(vendor__id=vendor_id).exclude(code='')

    if not items:
        return HttpResponseNotFound(
            u'No items found for "{0}".'.format(vendor.user.username))
    
    render_params = {
            'items': items,
            'bar_type': bar_type,
            'tag_type': tag_type,}
    
    return render(request, "app_items.html", render_params)


def get_barcode(request, data, ext):
    """
    Render the data as a barcode.

    :param request: HttpRequest object
    :type request: django.http.request.HttpRequest

    :param data: Data to render
    :type data: str

    :param ext: Filename extension of the preferred format
    :type ext: str

    :return: Response containing the raw image data
    :rtype: HttpResponse
    """
    if ext not in ('svg', 'png'):
        return HttpResponseBadRequest(u"Image extension not supported")

    if ext == 'svg':
        writer, mimetype = SVGWriter(), 'image/svg+xml'
    else:
        # FIXME: TypeError if PIL is not installed
        writer, mimetype = ImageWriter(), 'image/png'

    bar = barcode.Code128(data, writer=writer)

    response = HttpResponse(mimetype=mimetype)
    bar.write(response, {
        'text_distance': 4,
        'module_height': 10,
        'module_width': 0.4,
    })

    return response


def get_item_barcode(request, item_id, ext):
    """
    Get a barcode image for given item.

    :param request: HttpRequest object
    :type request: django.http.request.HttpRequest
    :param item_id: Item identifier
    :type item_id: str
    :param ext: Filename extension of the preferred format
    :type ext: str
    :return: Response containing raw image data
    :rtype: HttpResponse
    """
    item = get_object_or_404(Item, code=item_id)
    return get_barcode(request, item.code, ext)


def get_commands(request):
    bar_type = request.GET.get("format", "svg").lower()

    if bar_type not in ('svg', 'png'):
        return HttpResponseBadRequest(u"Image extension not supported")

    items = []
    code_item = namedtuple("CodeItem", "name code action")

    for c in Clerk.objects.all():
        code = c.id
        name = c.user.get_short_name()
        if len(name) == 0:
            name = c.user.get_username()

        cc = CommandCode.encode_code(CommandCode.START_CLERK, code)
        items.append(code_item(name=name, code=cc, action=ugettext(u"Start")))

        cc = CommandCode.encode_code(CommandCode.END_CLERK, code)
        items.append(code_item(name=name, code=cc, action=ugettext(u"End")))

    return render(request, "app_clerks.html", {'items': items, 'bar_type': bar_type})


def checkout_view(request):
    """
    Checkout view.

    :param request: HttpRequest object
    :type request: django.http.request.HttpRequest
    :return: Response containing the view.
    :rtype: HttpResponse
    """
    return render(request, "app_checkout.html")


def checkout_add_item(request):
    """
    Add item to receipt. Expects item code in POST.code and receipt id in
    POST.receipt.

    :param request: HttpRequest object
    :type request: django.http.request.HttpRequest
    :rtype: HttpResponse
    """
    pass


def checkout_del_item(request):
    """
    Remove item from receipt. Expects item code in POST.code and receipt id
    in POST.receipt.

    :param request: HttpRequest object.
    :type request: django.http.request.HttpRequest
    :rtype: HttpResponse
    """
    pass


def checkout_finish_receipt(request):
    """
    Finish receipt. Expects receipt id in POST.receipt.

    :param request: HttpRequest object.
    :type request: django.http.request.HttpRequest
    :rtype: HttpResponse
    """
    pass


def vendor_view(request):
    """
    Render main view for vendors.

    :rtype: HttpResponse
    """
    return HttpResponse('in construction...')


@sensitive_post_parameters()
def vendor_login(request):
    """
    On GET, render the login page. On POST, attempt login.

    :rtype: HttpResponse
    """
    # Based on django.contrib.auth.views.login().
    template_name = "app_vendor_login.html"

    destination = request.REQUEST.get('next')
    if not is_safe_url(destination, request.get_host()):
        destination = url.reverse('kirppu:vendor_view')

    if request.method == 'GET':
        return render(request, template_name, {
            'next': destination,
            'form': VendorAuthenticationForm(request),
        })

    elif request.method == 'POST':
        form = VendorAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth.login(request, form.get_user())
            return HttpResponseRedirect(destination)
        else:
            return render(request, template_name, {
                'next': destination,
                'form': form,
            })


@sensitive_post_parameters()
def vendor_signup(request):
    """
    On GET, render the sign-up page. On POST, attempt sign-up.

    :rtype: HttpResponse
    """
    template_name = "app_vendor_signup.html"

    if request.method == 'GET':
        return render(request, template_name, {
            'form': VendorCreationForm(),
        })

    elif request.method == 'POST':
        form = VendorCreationForm(data=request.POST)
        if form.is_valid():
            # Create and log in the user.
            user = form.save()
            user = auth.authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
            )
            auth.login(request, user)

            # Redirect to the vendor page.
            destination = url.reverse('kirppu:vendor_view')
            return HttpResponseRedirect(destination)

        else:
            return render(request, template_name, {'form': form})

def user_logout(request):
    """
    Logout a vendor or a clerk.
    """
    return auth_views.logout(
        request,
        template_name='app_logged_out.html',
        redirect_field_name='next',
    )
