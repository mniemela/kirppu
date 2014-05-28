from collections import namedtuple

import barcode
from barcode.writer import SVGWriter, ImageWriter

import django.contrib.auth as auth
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

from kirppu.app.forms import VendorAuthenticationForm
from kirppu.app.models import (
    Item,
    Event,
    CommandCode,
    Vendor,
)


def index(request):
    return HttpResponse("")


def get_items(request, sid, eid):
    """
    Get a page containing all items for vendor.

    :param request: HttpRequest object.
    :type request: django.http.request.HttpRequest
    :param sid: Vendor ID
    :type sid: str
    :param eid: Event ID
    :type eid: str
    :return: HttpResponse or HttpResponseBadRequest
    """
    bar_type = request.GET.get("format", "svg").lower()

    if bar_type not in ('svg', 'png'):
        return HttpResponseBadRequest(u"Image extension not supported")

    try:
        vendor = Vendor.objects.get(id=sid)
    except:
        return HttpResponseNotFound(u'Vendor not found.')
    try:
        event = Event.objects.get(id=eid)
    except:
        return HttpResponseNotFound(u'Event not found.')

    items = Item.objects.filter(vendor__id=sid, event__id=eid).exclude(code=u"")

    if not items:
        return HttpResponseNotFound(u'No items found for "%s" in "%s".' % (vendor.user.username, event.name))

    return render(request, "app_items.html", {'items': items, 'bar_type': bar_type})


def get_item_image(request, iid, ext):
    """
    Get a barcode image for given item.

    :param request: HttpRequest object
    :type request: django.http.request.HttpRequest
    :param iid: Item identifier
    :type iid: str
    :param ext: Extension/image type to be used
    :type ext: str
    :return: Response containing raw image data
    :rtype: HttpResponse
    """
    ext = ext.lower()
    if ext not in ('svg', 'png'):
        return HttpResponseBadRequest(u"Image extension not supported")

    if ext == 'svg':
        writer, mimetype = SVGWriter(), 'image/svg+xml'
    else:
        # FIXME: TypeError if PIL is not installed
        writer, mimetype = ImageWriter(), 'image/png'

    item = get_object_or_404(Item, code=iid)
    bar = barcode.Code128(item.code, writer=writer)

    response = HttpResponse(mimetype=mimetype)
    bar.write(response, {
        'text_distance': 4,
        'module_height': 10,
        'module_width': 0.4,
    })

    return response


def get_commands(request, eid):
    bar_type = request.GET.get("format", "svg").lower()

    if bar_type not in ('svg', 'png'):
        return HttpResponseBadRequest(u"Image extension not supported")

    # FIXME: OverflowError with very large eids
    eid = int(eid)
    event = get_object_or_404(Event, pk=eid)
    items = []
    code_item = namedtuple("CodeItem", "name code action")

    for c in event.clerks.all():
        code = event.get_clerk_code(c)
        name = c.get_short_name()
        if len(name) == 0:
            name = c.get_username()

        cc = CommandCode.encode_code(CommandCode.START_CLERK, code)
        items.append(code_item(name=name, code=cc, action=ugettext(u"Start")))

        cc = CommandCode.encode_code(CommandCode.END_CLERK, code)
        items.append(code_item(name=name, code=cc, action=ugettext(u"End")))

    return render(request, "app_clerks.html", {'items': items, 'bar_type': bar_type})


def get_command_image(request, iid, ext):
    """
    Get a barcode image for given item.

    :param request: HttpRequest object
    :type request: django.http.request.HttpRequest
    :param iid: Item identifier
    :type iid: str
    :param ext: Extension/image type to be used
    :type ext: str
    :return: Response containing raw image data
    :rtype: HttpResponse
    """
    ext = ext.lower()
    if len(ext) == 0:
        ext = "svg"
    if ext not in ('svg', 'png'):
        return HttpResponseBadRequest(u"Image extension not supported")

    if ext == 'svg':
        writer, mimetype = SVGWriter(), 'image/svg+xml'
    else:
        # FIXME: TypeError if PIL is not installed
        writer, mimetype = ImageWriter(), 'image/png'

    bar = barcode.Code128(iid, writer=writer)

    response = HttpResponse(mimetype=mimetype)
    bar.write(response, {
        'text_distance': 4,
        'module_height': 10,
        'module_width': 0.4,
    })

    return response


def checkout_view(request, eid):
    """
    Checkout view.

    :param request: HttpRequest object
    :type request: django.http.request.HttpRequest
    :param eid: Event id number
    :type eid: str
    :return: Response containing the view.
    :rtype: HttpResponse
    """
    return render(request, "app_checkout.html")


def checkout_add_item(request, eid):
    """
    Add item to receipt. Expects item code in POST.code and receipt id in
    POST.receipt.

    :param request: HttpRequest object
    :type request: django.http.request.HttpRequest
    :param eid:
    :type eid: str
    :rtype: HttpResponse
    """
    pass


def checkout_del_item(request, eid):
    """
    Remove item from receipt. Expects item code in POST.code and receipt id
    in POST.receipt.

    :param request: HttpRequest object.
    :type request: django.http.request.HttpRequest
    :param eid:
    :type eid: str
    :rtype: HttpResponse
    """
    pass


def checkout_finish_receipt(request, eid):
    """
    Finish receipt. Expects receipt id in POST.receipt.

    :param request: HttpRequest object.
    :type request: django.http.request.HttpRequest
    :param eid:
    :type eid: str
    :rtype: HttpResponse
    """
    pass


def vendor_view(request):
    """
    Render main view for vendors.
    """
    # TODO
    return HttpResponse('')


@sensitive_post_parameters()
def vendor_login(request):
    """
    On GET, render the login page. On POST, attempt login.
    """
    # Inspired by django.contrib.auth.views.
    destination = request.REQUEST.get('next')
    if not is_safe_url(destination, request.get_host()):
        destination = url.reverse('kirppu:vendor_view')

    def render_login_page(next_=None, form=None):
        form = (form if form is not None
                     else VendorAuthenticationForm(request))
        context = {'form': form, 'next': next_}
        context.update(csrf(request))
        return render(request, "app_vendor_login.html", context)

    if request.method == 'GET':
        return render_login_page(destination)

    elif request.method == 'POST':
        form = VendorAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth.login(request, form.get_user())
            return HttpResponseRedirect(destination)
        else:
            return render_login_page(destination, form)
