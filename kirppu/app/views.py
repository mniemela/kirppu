from collections import namedtuple
from decimal import Decimal, InvalidOperation
import decimal
import json
import re

import barcode
from barcode.writer import SVGWriter

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
from kirppu.app.utils import require_setting, PixelWriter


def index(request):
    return HttpResponse("")


@login_required
@require_http_methods(["POST"])
def item_add(request):
    vendor = Vendor.get_vendor(request.user)
    name = request.POST.get("name", "")
    price = request.POST.get("price", "")
    tag_type = request.POST.get("type", "short")
    suffix_str = request.POST.get("range", "")

    if not price:
        return HttpResponseBadRequest("Item must have a price.")

    price = price.replace(",", ".")
    try:
        price = Decimal(price).quantize(Decimal('0.1'), rounding=decimal.ROUND_UP)
    except InvalidOperation:
        return HttpResponseBadRequest("Price must be numeric.")

    # Round up to nearest 50 cents.
    remainder = price % Decimal('.5')
    if remainder > Decimal('0'):
        price += Decimal('.5') - remainder

    if price <= Decimal('0'):
        return HttpResponseBadRequest("Price too low.")
    elif price > Decimal('400'):
        return HttpResponseBadRequest("Price too high.")

    def expand_suffixes(input_str):
        """Turn 'a b 1 3-4' to ['a', 'b', '1', '3', '4']"""
        words = input_str.split()
        result = []

        for word in words:
            # Handle the range syntax as a special case.
            match = re.match(r"(\d+)-(\d+)$", word)
            if match:
                # Turn '1-3' to ['1', '2', '3'] and so on
                left, right = map(int, match.groups())
                if abs(left - right) + 1 >= 100:
                    raise ValueError('Maximum of 100 items allowed by a single range statement.')
                if left > right:
                    left, right = right, left
                result.extend(map(str, range(left, right + 1)))
            else:
                result.append(word)

        return result

    try:
        suffixes = expand_suffixes(suffix_str)
    except ValueError as e:
        return HttpResponseBadRequest(e.message)

    if not suffixes:
        # If there are no suffixes the name is added as is just once.
        # This is equivalent to adding empty string as suffix.
        suffixes.append('')

    # Create the items and construct a response containing all the items that have been added.
    response = []
    for suffix in suffixes:
        suffixed_name = name + suffix
        item = Item.new(name=suffixed_name, price=str(price), vendor=vendor, type=tag_type, state=Item.ADVERTISED)
        item_dict = {
            'vendor_id': vendor.id,
            'code': item.code,
            'name': item.name,
            'price': str(item.price).replace('.', ','),
            'type': item.type,
        }
        response.append(item_dict)

    return HttpResponse(json.dumps(response), 'application/json')


@login_required
@require_http_methods(['POST'])
def item_to_print(request, code):
    vendor = Vendor.get_vendor(request.user)

    item = Item.objects.get(code=code, vendor=vendor)
    if not item:
        return HttpResponseBadRequest('No such item.')

    # Create a duplicate of the item with a new code and hide the old item.
    # This way, even if the user forgets to attach the new tags, the old
    # printed tag is still in the system.
    new_item = Item.new(name=item.name, price=item.price, vendor=item.vendor, type=item.type, state=Item.ADVERTISED)
    item_dict = {
        'vendor_id': new_item.vendor_id,
        'code': new_item.code,
        'name': new_item.name,
        'price': str(new_item.price).replace('.', ','),
        'type': new_item.type,
    }

    item.hidden = True
    item.save()

    return HttpResponse(json.dumps(item_dict), 'application/json')


@require_http_methods(["DELETE"])
def item_delete(request, code):
    item = Item.get_item_by_barcode(code)

    item.printed = True
    item.save()

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
    price = request.POST.get("value", "0")
    price = price.replace(",", ".")

    price = Decimal(price).quantize(Decimal('.1'), rounding=decimal.ROUND_UP)

    # Round up to nearest 50 cents.
    remainder = price % Decimal('.5')
    if remainder > Decimal('0'):
        price += Decimal('.5') - remainder

    if price <= Decimal('0'):
        return HttpResponseBadRequest("Price too low.")
    elif price > Decimal('400'):
        return HttpResponseBadRequest("Price too high.")

    item = Item.get_item_by_barcode(code)
    item.price = str(price)
    item.save()

    return HttpResponse(str(price).replace(".", ","))


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
@require_http_methods(["POST"])
def all_to_print(request):
    vendor = Vendor.get_vendor(request.user)

    items = Item.objects.filter(vendor=vendor).filter(printed=False)

    for item in items:
        item.printed = True
        item.save()

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

    # Use PNG if we can because SVGs from pyBarcode are huge.
    default_format = 'png' if PixelWriter else 'svg'

    bar_type = request.GET.get("format", default_format).lower()
    tag_type = request.GET.get("tag", "short").lower()

    if bar_type not in ('svg', 'png', 'gif', 'bmp'):
        return HttpResponseBadRequest(u"Image extension not supported")
    if tag_type not in ('short', 'long'):
        return HttpResponseBadRequest(u"Tag type not supported")

    vendor = Vendor.get_vendor(request.user)
    items = Item.objects.filter(vendor=vendor).filter(printed=False)
    printed_items = Item.objects.filter(vendor=vendor).filter(printed=True)
    printed_items = printed_items.filter(hidden=False)

    # Order from newest to oldest, because that way new items are added
    # to the top and the user immediately sees them without scrolling
    # down.
    items = items.order_by('-id')

    render_params = {
        'items': items,
        'printed_items': printed_items,
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
    if ext not in ('svg', 'png', 'gif', 'bmp'):
        return HttpResponseBadRequest(u"Image extension not supported")

    # FIXME: TypeError if PIL is not installed
    writer, mimetype = PixelWriter(format=ext), 'image/' + ext

    bar = barcode.Code128(data, writer=writer)

    response = HttpResponse(mimetype=mimetype)
    bar.write(response, {
        'module_width': 1,  # pixels per smallest line
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
