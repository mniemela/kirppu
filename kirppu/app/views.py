from collections import namedtuple
from decimal import Decimal, InvalidOperation
import decimal
import json
import re
import urllib

import barcode

from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden)
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.conf import settings
import django.core.urlresolvers as url
from django.utils.http import is_safe_url
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from kirppu.app.models import (
    Item,
    Clerk,
    Vendor,
)
from kirppu.app.utils import require_setting, PixelWriter, require_vendor_open, is_vendor_open
from templatetags.kirppu_tags import get_dataurl


def index(request):
    return redirect("kirppu:vendor_view")


@login_required
@require_http_methods(["POST"])
@require_vendor_open
def item_add(request):
    vendor = Vendor.get_vendor(request.user)
    name = request.POST.get("name", u"").strip()
    price = request.POST.get("price", "")
    tag_type = request.POST.get("type", "short")
    suffix_str = request.POST.get("range", u"")

    if not price:
        return HttpResponseBadRequest(_(u"Item must have a price."))

    price = price.replace(",", ".")
    try:
        price = Decimal(price).quantize(Decimal('0.1'), rounding=decimal.ROUND_UP)
    except InvalidOperation:
        return HttpResponseBadRequest(_(u"Price must be numeric."))

    # Round up to nearest 50 cents.
    remainder = price % Decimal('.5')
    if remainder > Decimal('0'):
        price += Decimal('.5') - remainder

    if price <= Decimal('0'):
        return HttpResponseBadRequest(_(u"Price too low. (min 0.5 euros)"))
    elif price > Decimal('400'):
        return HttpResponseBadRequest(_(u"Price too high. (max 400 euros)"))

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
                if abs(left - right) + 1 > 100:
                    return None
                if left > right:
                    left, right = right, left
                result.extend(map(unicode, range(left, right + 1)))
            else:
                result.append(word)

        return result

    suffixes = expand_suffixes(suffix_str)
    if suffixes is None:
        return HttpResponseBadRequest(_(u'Maximum of 100 items allowed by a single range statement.'))

    if not suffixes:
        # If there are no suffixes the name is added as is just once.
        # This is equivalent to adding empty string as suffix.
        suffixes.append(u"")

    item_cnt = Item.objects.filter(vendor=vendor).count()

    # Create the items and construct a response containing all the items that have been added.
    response = []
    max_items = settings.KIRPPU_MAX_ITEMS_PER_VENDOR
    for suffix in suffixes:
        if item_cnt >= max_items:
            error_msg = _(u"You have %(max_items)s items, which is the maximum. No more items can be registered.")
            return HttpResponseBadRequest(error_msg % {'max_items': max_items})
        item_cnt += 1

        suffixed_name = (name + u" " + suffix).strip()
        item = Item.new(name=suffixed_name, price=str(price), vendor=vendor, type=tag_type, state=Item.ADVERTISED)
        item_dict = {
            'vendor_id': vendor.id,
            'code': item.code,
            'barcode_dataurl': get_dataurl(item.code, 'png'),
            'name': item.name,
            'price': str(item.price_fmt).replace('.', ','),
            'type': item.type,
        }
        response.append(item_dict)

    return HttpResponse(json.dumps(response), 'application/json')


@login_required
@require_http_methods(['POST'])
def item_to_not_printed(request, code):
    vendor = Vendor.get_vendor(request.user)
    item = get_object_or_404(Item.objects, code=code, vendor=vendor)

    if settings.KIRPPU_COPY_ITEM_WHEN_UNPRINTED:
        # Create a duplicate of the item with a new code and hide the old item.
        # This way, even if the user forgets to attach the new tags, the old
        # printed tag is still in the system.
        if not is_vendor_open():
            return HttpResponseForbidden("Registration is closed")

        new_item = Item.new(name=item.name, price=item.price,
                vendor=item.vendor, type=item.type, state=Item.ADVERTISED)
        item.hidden = True
    else:
        item.printed = False
        new_item = item
    item.save()

    item_dict = {
        'vendor_id': new_item.vendor_id,
        'code': new_item.code,
        'barcode_dataurl': get_dataurl(item.code, 'png'),
        'name': new_item.name,
        'price': str(new_item.price).replace('.', ','),
        'type': new_item.type,
    }

    return HttpResponse(json.dumps(item_dict), 'application/json')


@login_required
@require_http_methods(["POST"])
def item_to_printed(request, code):
    vendor = Vendor.get_vendor(request.user)
    item = get_object_or_404(Item.objects, code=code, vendor=vendor)

    item.printed = True
    item.save()

    return HttpResponse()


@login_required
@require_http_methods(["POST"])
@require_vendor_open
def item_update_price(request, code):
    price = request.POST.get("value", "0")
    if len(price) > 8:
        return HttpResponseBadRequest("Invalid price.")
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

    vendor = Vendor.get_vendor(request.user)
    item = get_object_or_404(Item.objects, code=code, vendor=vendor)

    if item.is_locked():
        return HttpResponseBadRequest("Item has been brought to event. Price can't be changed.")

    item.price = str(price)
    item.save()

    return HttpResponse(str(price).replace(".", ","))


@login_required
@require_http_methods(["POST"])
@require_vendor_open
def item_update_name(request, code):
    name = request.POST.get("value", "no name")
    
    name = name[:80]

    vendor = Vendor.get_vendor(request.user)
    item = get_object_or_404(Item.objects, code=code, vendor=vendor)

    if item.is_locked():
        return HttpResponseBadRequest("Item has been brought to event. Name can't be changed.")

    item.name = name
    item.save()

    return HttpResponse(name)


@login_required
@require_http_methods(["POST"])
def item_update_type(request, code):
    tag_type = request.POST.get("tag_type", None)

    vendor = Vendor.get_vendor(request.user)
    item = get_object_or_404(Item.objects, code=code, vendor=vendor)
    item.type = tag_type
    item.save()
    return HttpResponse()


@login_required
@require_http_methods(["POST"])
def all_to_print(request):
    vendor = Vendor.get_vendor(request.user)
    items = Item.objects.filter(vendor=vendor).filter(printed=False)

    items.update(printed=True)

    return HttpResponse()


def _vendor_menu_contents(request):
    """
    Generate menu for Vendor views.
    Returned tuple contains entries for the menu, each entry containing a
    name, url, and flag indicating whether the entry is currently active
    or not.

    :param request: Current request being processed.
    :return: List of menu items containing name, url and active fields.
    :rtype: tuple[MenuItem,...]
    """
    active = request.resolver_match.view_name
    menu_item = namedtuple("MenuItem", "name url active")
    fill = lambda name, func: menu_item(name, url.reverse(func), func == active)

    return (
        fill(_(u"Home"), "kirppu:vendor_view"),
        fill(_(u"Item list"), "kirppu:page"),
    )


@login_required
@require_http_methods(["GET"])
def get_items(request):
    """
    Get a page containing all items for vendor.

    :param request: HttpRequest object.
    :type request: django.http.request.HttpRequest
    :return: HttpResponse or HttpResponseBadRequest
    """

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

        'profile_url': settings.PROFILE_URL,

        'is_registration_open': is_vendor_open(),
        'menu': _vendor_menu_contents(request),
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


@login_required
def get_clerk_codes(request):
    if not request.user.is_staff:
        return HttpResponseForbidden(_(u"Forbidden"))

    # Use PNG if we can because SVGs from pyBarcode are huge.
    default_format = 'png' if PixelWriter else 'svg'

    bar_type = request.GET.get("format", default_format).lower()

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


def vendor_view(request):
    """
    Render main view for vendors.

    :rtype: HttpResponse
    """
    user = request.user

    if user.is_authenticated():
        vendor = Vendor.get_vendor(user)
        items = Item.objects.filter(vendor=vendor)
    else:
        items = []

    context = {
        'user': user,
        'items': items,

        'total_price': sum(i.price for i in items),
        'num_total':   len(items),
        'num_printed': len(filter(lambda i: i.printed, items)),

        'profile_url': settings.PROFILE_URL,
        'menu': _vendor_menu_contents(request),
    }
    return render(request, "app_frontpage.html", context)


def login_view(request):
    """
    Redirect to Kompassi login page.
    """
    destination = request.REQUEST.get('next')
    if not is_safe_url(destination, request.get_host()):
        destination = request.build_absolute_uri(url.reverse('kirppu:vendor_view'))
    login_url = '{0}?{1}'.format(
        settings.LOGIN_URL,
        urllib.urlencode({'next': destination}),
    )
    return redirect(login_url)


def logout_view(request):
    """
    Log out user and redirect to Kompassi logout page.
    """
    logout(request)
    destination = request.REQUEST.get('next')
    if not is_safe_url(destination, request.get_host()):
        destination = request.build_absolute_uri(url.reverse('kirppu:vendor_view'))
    logout_url = '{0}?{1}'.format(
        settings.LOGOUT_URL,
        urllib.urlencode({'next': destination}),
    )
    return redirect(logout_url)
