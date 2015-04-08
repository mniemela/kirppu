import inspect

from django.contrib.auth import get_user_model

from django.db.models import Q
from django.http import Http404
from django.http.response import (
    HttpResponse,
)
from django.shortcuts import (
    get_object_or_404,
    render,
)
from django.utils.translation import ugettext as _i
from django.utils.timezone import now

from .models import (
    Item,
    Receipt,
    Clerk,
    Counter,
    ReceiptItem,
    Vendor,
    UserAdapter,
)

from . import ajax_util
from .ajax_util import (
    AjaxError,
    get_counter,
    get_clerk,
    require_counter_validated,
    require_clerk_login,
    RET_BAD_REQUEST,
    RET_FORBIDDEN,
    RET_CONFLICT,
    RET_AUTH_FAILED,
    RET_LOCKED,
)


def raise_if_item_not_available(item):
    """Raise appropriate AjaxError if item is not in buyable state."""
    if item.state == Item.STAGED:
        # Staged somewhere other?
        raise AjaxError(RET_LOCKED, 'Item is already staged to be sold.')
    elif item.state == Item.ADVERTISED:
        return 'Item has not been brought to event.'
    elif item.state in (Item.SOLD, Item.COMPENSATED):
        raise AjaxError(RET_CONFLICT, 'Item has already been sold.')
    elif item.state == Item.RETURNED:
        raise AjaxError(RET_CONFLICT, 'Item has already been returned to owner.')
    return None


# Registry for ajax functions. Maps function names to AjaxFuncs.
AJAX_FUNCTIONS = {}


def _register_ajax_func(func):
    AJAX_FUNCTIONS[func.name] = func


def ajax_func(url, method='POST', counter=True, clerk=True):
    def decorator(func):
        # Get argspec before any decoration.
        (args, _, _, _) = inspect.getargspec(func)

        if counter:
            func = require_counter_validated(func)
        if clerk:
            func = require_clerk_login(func)
        return ajax_util.ajax_func(
            url,
            _register_ajax_func,
            method,
            args[1:]
        )(func)
    return decorator


def checkout_js(request):
    """
    Render the JavaScript file that defines the AJAX API functions.
    """
    context = {
        'funcs': AJAX_FUNCTIONS,
        'api_name': 'Api',
    }
    return render(
        request,
        "kirppu/app_ajax_api.js",
        context,
        content_type="application/javascript"
    )


def _get_item_or_404(code):
    try:
        item = Item.get_item_by_barcode(code)
    except Item.DoesNotExist:
        item = None

    if item is None:
        raise Http404(_i(u"No item found matching '{0}'").format(code))
    return item


def item_mode_change(code, from_, to, message_if_not_first=None):
    item = _get_item_or_404(code)
    if not isinstance(from_, tuple):
        from_ = (from_,)
    if item.state in from_:
        if item.hidden:
            # If an item is brought to the event, even though the user deleted it, it should begin showing again in
            # users list. The same probably applies to any interaction with the item.
            item.hidden = False

        old_state = item.state
        item.state = to
        item.save()
        ret = item.as_dict()
        if message_if_not_first is not None and len(from_) > 1 and old_state != from_[0]:
            ret.update(_message=message_if_not_first)
        return ret

    else:
        # Item not in expected state.
        raise AjaxError(
            RET_CONFLICT,
            _i(u"Unexpected item state: {state}").format(state=item.state),
        )


@ajax_func('^clerk/login$', clerk=False, counter=False)
def clerk_login(request, code, counter):
    try:
        counter_obj = Counter.objects.get(identifier=counter)
    except Counter.DoesNotExist:
        raise AjaxError(RET_AUTH_FAILED, _i(u"Counter has gone missing."))

    try:
        clerk = Clerk.by_code(code)
    except ValueError as ve:
        raise AjaxError(RET_AUTH_FAILED, repr(ve))

    if clerk is None:
        raise AjaxError(RET_AUTH_FAILED, _i(u"No such clerk."))

    clerk_data = clerk.as_dict()
    clerk_data['overseer_enabled'] = clerk.user.has_perm('kirppu.oversee')

    active_receipts = Receipt.objects.filter(clerk=clerk, status=Receipt.PENDING)
    if active_receipts:
        if len(active_receipts) > 1:
            clerk_data["receipts"] = [receipt.as_dict() for receipt in active_receipts]
            clerk_data["receipt"] = "MULTIPLE"
        else:
            receipt = active_receipts[0]
            request.session["receipt"] = receipt.pk
            clerk_data["receipt"] = receipt.as_dict()

    request.session["clerk"] = clerk.pk
    request.session["clerk_token"] = clerk.access_key
    request.session["counter"] = counter_obj.pk
    return clerk_data


@ajax_func('^clerk/logout$', clerk=False, counter=False)
def clerk_logout(request):
    """
    Logout currently logged in clerk.
    """
    clerk_logout_fn(request)
    return HttpResponse()


def clerk_logout_fn(request):
    """
    The actual logout procedure that can be used from elsewhere too.

    :param request: Active request, for session access.
    """
    for key in ["clerk", "clerk_token", "counter"]:
        request.session.pop(key, None)


@ajax_func('^counter/validate$', clerk=False, counter=False)
def counter_validate(request, code):
    """
    Validates the counter identifier and returns its exact form, if it is
    valid.
    """
    try:
        counter = Counter.objects.get(identifier__iexact=code)
    except Counter.DoesNotExist:
        raise AjaxError(RET_AUTH_FAILED)

    return {"counter": counter.identifier,
            "name": counter.name}


@ajax_func('^item/find$', method='GET')
def item_find(request, code):
    item = _get_item_or_404(code)
    value = item.as_dict()
    if "available" in request.GET:
        message = raise_if_item_not_available(item)
        if message is not None:
            value.update(_message=message)
    return value


@ajax_func('^item/search$', method='GET')
def item_search(request, query, code, vendor, min_price, max_price, item_type, item_state):
    if not get_clerk(request).user.has_perm('kirppu.oversee'):
        raise AjaxError(RET_FORBIDDEN, _i(u"Access denied."))

    clauses = []

    types = item_type.split()
    if types:
        clauses.append(Q(itemtype__in=types))

    code = code.strip()
    if code:
        clauses.append(Q(code__contains=code))

    if vendor:
        clauses.append(Q(vendor=vendor))

    states = item_state.split()
    if states:
        clauses.append(Q(state__in=states))

    for part in query.split():
        clauses.append(Q(name__icontains=part))

    try:
        clauses.append(Q(price__gte=float(min_price)))
    except ValueError:
        pass

    try:
        clauses.append(Q(price__lte=float(max_price)))
    except ValueError:
        pass

    results = []

    for item in Item.objects.filter(*clauses).all():
        item_dict = item.as_dict()
        item_dict['vendor'] = item.vendor.as_dict()
        results.append(item_dict)

    return results


@ajax_func('^item/list$', method='GET')
def item_list(request, vendor):
    items = Item.objects.filter(vendor__id=vendor)
    return map(lambda i: i.as_dict(), items)


@ajax_func('^item/checkin$')
def item_checkin(request, code):
    return item_mode_change(code, Item.ADVERTISED, Item.BROUGHT)


@ajax_func('^item/checkout$')
def item_checkout(request, code):
    return item_mode_change(code, (Item.BROUGHT, Item.ADVERTISED), Item.RETURNED, _i(u"Item was not brought to event."))


@ajax_func('^item/compensate$')
def item_compensate(request, code):
    return item_mode_change(code, Item.SOLD, Item.COMPENSATED)


@ajax_func('^vendor/get$', method='GET')
def vendor_get(request, id):
    try:
        vendor = Vendor.objects.get(pk=int(id))
    except (ValueError, Vendor.DoesNotExist):
        raise AjaxError(RET_BAD_REQUEST, _i(u"Invalid vendor id"))
    else:
        return vendor.as_dict()


@ajax_func('^vendor/find$', method='GET')
def vendor_find(request, q):
    clauses = [Q(vendor__isnull=False)]

    for part in q.split():
        clause = (
              Q(**UserAdapter.phone_query(part))
            | Q(username__icontains=part)
            | Q(first_name__icontains=part)
            | Q(last_name__icontains=part)
            | Q(email__icontains=part)
        )
        try:
            clause = clause | Q(vendor__id=int(part))
        except ValueError:
            pass

        clauses.append(clause)

    return [
        u.vendor.as_dict()
        for u in get_user_model().objects.filter(*clauses).all()
    ]


@ajax_func('^receipt/start$')
def receipt_start(request):
    receipt = Receipt()
    receipt.clerk = get_clerk(request)
    receipt.counter = get_counter(request)

    receipt.save()

    request.session["receipt"] = receipt.pk
    return receipt.as_dict()


@ajax_func('^item/reserve$')
def item_reserve(request, code):
    item = _get_item_or_404(code)
    receipt_id = request.session["receipt"]
    receipt = get_object_or_404(Receipt, pk=receipt_id)

    message = raise_if_item_not_available(item)
    if item.state in (Item.ADVERTISED, Item.BROUGHT, Item.MISSING):
        item.state = Item.STAGED
        item.save()

        ReceiptItem.objects.create(item=item, receipt=receipt)
        # receipt.items.create(item=item)
        receipt.calculate_total()
        receipt.save()

        ret = item.as_dict()
        ret.update(total=receipt.total_cents)
        if message is not None:
            ret.update(_message=message)
        return ret
    else:
        # Not in expected state.
        raise AjaxError(RET_CONFLICT)


@ajax_func('^item/release$')
def item_release(request, code):
    item = _get_item_or_404(code)
    receipt_id = request.session["receipt"]
    receipt = get_object_or_404(Receipt, pk=receipt_id)

    last_added_item = ReceiptItem.objects\
        .filter(receipt=receipt, item=item, action=ReceiptItem.ADD)\
        .order_by("-add_time")

    if len(last_added_item) == 0:
        raise AjaxError(RET_CONFLICT, _i(u"Item is not added to receipt."))
    assert len(last_added_item) == 1

    last_added_item = last_added_item[0]
    last_added_item.action = ReceiptItem.REMOVED_LATER
    last_added_item.save()

    removal_entry = ReceiptItem(item=item, receipt=receipt, action=ReceiptItem.REMOVE)
    removal_entry.save()

    receipt.calculate_total()
    receipt.save()

    item.state = Item.BROUGHT
    item.save()

    return removal_entry.as_dict()


@ajax_func('^receipt/finish$')
def receipt_finish(request):
    receipt_id = request.session["receipt"]
    receipt = get_object_or_404(Receipt, pk=receipt_id)
    if receipt.status != Receipt.PENDING:
        raise AjaxError(RET_CONFLICT)

    receipt.sell_time = now()
    receipt.status = Receipt.FINISHED
    receipt.save()

    Item.objects.filter(receipt=receipt, receiptitem__action=ReceiptItem.ADD).update(state=Item.SOLD)

    del request.session["receipt"]
    return receipt.as_dict()


@ajax_func('^receipt/abort$')
def receipt_abort(request):
    receipt_id = request.session["receipt"]
    receipt = get_object_or_404(Receipt, pk=receipt_id)

    if receipt.status != Receipt.PENDING:
        raise AjaxError(RET_CONFLICT)

    # For all ADDed items, add REMOVE-entries and return the real Item's back to available.
    added_items = ReceiptItem.objects.filter(receipt_id=receipt_id, action=ReceiptItem.ADD)
    for receipt_item in added_items.only("item"):
        item = receipt_item.item

        ReceiptItem(item=item, receipt=receipt, action=ReceiptItem.REMOVE).save()

        item.state = Item.BROUGHT
        item.save()

    # Update ADDed items to be REMOVED_LATER. This must be done after the real Items have
    # been updated, and the REMOVE-entries added, as this will change the result set of
    # the original added_items -query (to always return zero entries).
    added_items.update(action=ReceiptItem.REMOVED_LATER)

    # End the receipt. (Must be done after previous updates, so calculate_total calculates
    # correct sum.)
    receipt.sell_time = now()
    receipt.status = Receipt.ABORTED
    receipt.calculate_total()
    receipt.save()

    del request.session["receipt"]
    return receipt.as_dict()


def _get_receipt_data_with_items(**kwargs):
    receipt = get_object_or_404(Receipt, **kwargs)
    receipt_items = ReceiptItem.objects.filter(receipt_id=receipt.pk).order_by("add_time")

    data = receipt.as_dict()
    data["items"] = [item.as_dict() for item in receipt_items]
    return data


@ajax_func('^receipt$', method='GET')
def receipt_get(request):
    """
    Find receipt by receipt id or one item in the receipt.
    """
    if "id" in request.GET:
        receipt_id = int(request.GET.get("id"))
    elif "item" in request.GET:
        item_code = request.GET.get("item")
        receipt_id = get_object_or_404(ReceiptItem, item__code=item_code, action=ReceiptItem.ADD).receipt_id
    else:
        raise AjaxError(RET_BAD_REQUEST)
    return _get_receipt_data_with_items(pk=receipt_id)


@ajax_func('^receipt/activate$')
def receipt_activate(request):
    """
    Activate previously started pending receipt.
    """
    clerk = request.session["clerk"]
    receipt_id = int(request.POST.get("id"))
    data = _get_receipt_data_with_items(pk=receipt_id, clerk__id=clerk, status=Receipt.PENDING)
    request.session["receipt"] = receipt_id
    return data


@ajax_func('^barcode$', counter=False, clerk=False)
def get_barcodes(request, codes=None):
    """
    Get barcode images for a code, or list of codes.

    :param codes: Either list of codes, or a string, encoded in Json string.
    :type codes: str
    :return: List of barcode images encoded in data-url.
    :rtype: list[str]
    """
    from templatetags.kirppu_tags import barcode_dataurl
    from json import loads

    codes = loads(codes)
    if type(codes) in (str, unicode):
        codes = [codes]

    # XXX: This does ignore the width assertion. Beware with style sheets...
    outs = [
        barcode_dataurl(code, "png", None)
        for code in codes
    ]
    return outs


@ajax_func('^item/abandon$')
def items_abandon(request, vendor):
    """
    Set all of the vendor's 'brought to event' and 'missing' items to abandoned
    The view is expected to refresh itself
    """
    items = Item.objects.filter(vendor__id=vendor)
    for item in items:
        if item.state in (Item.BROUGHT, Item.MISSING):
            item.abandoned = True
            item.save()
    return
