from collections import namedtuple
import json

import barcode
from barcode.writer import SVGWriter, ImageWriter

from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden)
from django.shortcuts import (
    render,
    redirect,
)
from django.conf import settings
from django.utils.translation import ugettext
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _i

from kirppu.app.models import (
    Item,
    Clerk,
    CommandCode,
    Vendor,
)
from kirppu.app.utils import require_setting


def index(request):
    return HttpResponse("")


@login_required
@require_http_methods(["POST"])
def item_add(request):
    vendor = Vendor.get_vendor(request.user)
    print "vendor_id", request.user
    name = request.POST.get("name", "")
    price = request.POST.get("price", "")
    tag_type = request.POST.get("type", "short")

    item = Item.new(name=name, price=price, vendor=vendor, type=tag_type, state=Item.ADVERTISED)

    response = {
        'vendor_id': vendor.id,
        'code': item.code,
        'name': item.name,
        'price': item.price,
        'type': item.type,
    }
    return HttpResponse(json.dumps(response), 'application/json')


@require_http_methods(["DELETE"])
def item_delete(request, code):
    item = Item.get_item_by_barcode(code)

    if item.state == Item.ADVERTISED:
        item.delete()

    return HttpResponse()


@login_required
@require_http_methods(["DELETE"])
def item_view(request, code):
    # GET and PUT methods might be put here in the future.
    if request.method == 'DELETE':
        return item_delete(request, code)


@login_required
@require_http_methods(["POST"])
def item_update_price(request, code):
    str_price = request.POST.get("value", "0")
    str_price = str_price.replace(",", ".")
    
    try:
        cents = float(str_price) * 100  # price in cents
    except ValueError:
        cents = 0
    
    # Round up to nearest 50 cents.---
    if cents % 50 > 0:
        cents += 50 - cents % 50

    if cents == 0:
        return HttpResponseBadRequest("Na a!")
    
    str_euros = str(cents / 100.0)

    item = Item.get_item_by_barcode(code)
    item.price = str_euros
    item.save()

    return HttpResponse(str_euros.replace(".", ","))


@login_required
@require_http_methods(["POST"])
def item_update_name(request, code):
    name = request.POST.get("value", "no name")
    
    name = name[:80]

    item = Item.get_item_by_barcode(code)
    item.name = name
    item.save()

    return HttpResponse(name)


@login_required
@require_http_methods(["POST"])
def item_update_type(request, code):
    tag_type = request.POST.get("tag_type", None)

    item = Item.get_item_by_barcode(code)
    item.type = tag_type
    item.save()
    return HttpResponse()


@login_required
@require_http_methods(["DELETE"])
def delete_all_items(request):
    vendor = Vendor.get_vendor(request.user)

    items = Item.objects.filter(vendor=vendor)

    # Only allow deleting of items that have not been brought to the event yet.
    items = items.filter(state=Item.ADVERTISED)

    items.delete()

    return HttpResponse()


@login_required
@require_http_methods(["GET", "DELETE"])
def get_items(request):
    """
    Get a page containing all items for vendor.

    :param request: HttpRequest object.
    :type request: django.http.request.HttpRequest
    :return: HttpResponse or HttpResponseBadRequest
    """
    if request.method == "DELETE":
        return delete_all_items(request)

    bar_type = request.GET.get("format", "svg").lower()
    tag_type = request.GET.get("tag", "short").lower()

    if bar_type not in ('svg', 'png'):
        return HttpResponseBadRequest(u"Image extension not supported")
    if tag_type not in ('short', 'long'):
        return HttpResponseBadRequest(u"Tag type not supported")

    vendor = Vendor.get_vendor(request.user)
    items = Item.objects.filter(vendor=vendor).exclude(code='')

    render_params = {
        'items': items,
        'bar_type': bar_type,
        'tag_type': tag_type,
    }

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


@login_required
def get_clerk_codes(request):
    if not request.user.is_staff:
        return HttpResponseForbidden(_i(u"Forbidden"))
    bar_type = request.GET.get("format", "svg").lower()

    if bar_type not in ('svg', 'png'):
        return HttpResponseBadRequest(u"Image extension not supported")

    items = []
    code_item = namedtuple("CodeItem", "name code")

    for c in Clerk.objects.filter(access_key__isnull=False):
        code = c.get_code()
        if c.user is not None:
            name = c.user.get_short_name()
            if len(name) == 0:
                name = c.user.get_username()
        else:
            name = ""

        items.append(code_item(name=name, code=code))

    return render(request, "app_clerks.html", {'items': items, 'bar_type': bar_type})


# Access control by settings.
# CSRF is not generated if the Checkout-mode is not activated in settings.
@require_setting("KIRPPU_CHECKOUT_ACTIVE", True)
@ensure_csrf_cookie
def checkout_view(request):
    """
    Checkout view.

    :param request: HttpRequest object
    :type request: django.http.request.HttpRequest
    :return: Response containing the view.
    :rtype: HttpResponse
    """
    return render(request, "app_checkout.html")


@login_required
def vendor_view(request):
    """
    Render main view for vendors.

    :rtype: HttpResponse
    """
    return HttpResponse(
        u'hello {first_name} {last_name}!'
        u''.format(**request.user.__dict__)
    )


def logout_view(request):
    """
    Log out user and redirect to Kompassi logout page.
    """
    logout(request)
    return redirect(settings.LOGOUT_URL)
