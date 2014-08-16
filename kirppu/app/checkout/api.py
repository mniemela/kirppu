from functools import wraps
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext as _i
from django.utils.timezone import now
from kirppu.app.models import Item, Receipt, Clerk, Counter, ReceiptItem
from kirppu.app.utils import ajax_request

# Some HTTP Status codes that are used here.
RET_BAD_REQUEST = 400  # Bad request
RET_UNAUTHORIZED = 401  # Unauthorized, though, not expecting Basic Auth...
RET_CONFLICT = 409  # Conflict
RET_AUTH_FAILED = 419  # Authentication timeout
RET_LOCKED = 423  # Locked resource
RET_OK = 200  # OK


def _get_item_or_404(code):
    try:
        item = Item.get_item_by_barcode(code)
    except Item.DoesNotExist:
        item = None

    if item is None:
        raise Http404(_i(u"No item found matching '{0}'").format(code))
    return item


def require_clerk(fn):
    @wraps(fn)
    def inner(request, *args, **kwargs):
        if "clerk" not in request.session or\
                "clerk_token" not in request.session or\
                "counter" not in request.session:
            return RET_UNAUTHORIZED, _i(u"Not logged in.")

        clerk_id = request.session["clerk"]
        clerk_token = request.session["clerk_token"]

        try:
            clerk_object = Clerk.objects.get(pk=clerk_id)
        except Clerk.DoesNotExist:
            return RET_UNAUTHORIZED, _i(u"Clerk not found.")

        if clerk_object.access_key != clerk_token:
            return RET_UNAUTHORIZED, _i(u"Bye.")

        return fn(request, clerk_object, *args, **kwargs)
    return inner


def require_counter(fn):
    @wraps(fn)
    def inner(request, *args, **kwargs):
        if "counter" not in request.session:
            return RET_UNAUTHORIZED, _i(u"Not logged in.")

        counter_id = request.session["counter"]
        try:
            counter_object = Counter.objects.get(pk=counter_id)
        except Counter.DoesNotExist:
            return RET_UNAUTHORIZED, _i(u"Counter has gone missing.")

        return fn(request, counter_object, *args, **kwargs)
    return inner


@require_POST
@ajax_request
def login_clerk(request):
    if "code" not in request.POST or "counter" not in request.POST:
        return RET_BAD_REQUEST

    code = request.POST["code"]
    counter_ident = request.POST["counter"]

    clerk = Clerk.by_code(code)
    if clerk is None:
        return RET_AUTH_FAILED, _i(u"Unauthorized.")

    try:
        counter = Counter.objects.get(identifier=counter_ident)
    except Counter.DoesNotExist:
        return RET_AUTH_FAILED, _i(u"Counter has gone missing.")

    request.session["clerk"] = clerk.pk
    request.session["clerk_token"] = clerk.access_key
    request.session["counter"] = counter.pk
    return clerk.as_dict()


@require_POST
@ajax_request
def logout_clerk(request):
    """
    Logout currently logged in clerk.
    """
    del request.session["clerk"]
    del request.session["clerk_token"]
    del request.session["counter"]
    return RET_OK


@require_POST
@ajax_request
def validate_counter(request):
    """
    Validates the counter identifier and returns its exact form, if it is valid. The exact form
    must be supplied to login_clerk.
    """
    if "code" not in request.POST:
        return RET_BAD_REQUEST

    code = request.POST["code"]

    try:
        counter = Counter.objects.get(identifier__iexact=code)
    except Counter.DoesNotExist:
        return RET_AUTH_FAILED

    return {"counter": counter.identifier,
            "name": counter.name}


@ajax_request
@require_counter
def get_item(request, *args):
    item = _get_item_or_404(request.GET["code"])
    return item.as_dict()


@require_POST
@ajax_request
@require_clerk
@require_counter
def start_receipt(request, counter, clerk):
    receipt = Receipt()
    receipt.clerk = clerk
    receipt.counter = counter

    receipt.save()

    request.session["receipt"] = receipt.pk
    return receipt.as_dict()


@require_POST
@ajax_request
@require_clerk
def reserve_item_for_receipt(request, clerk):
    item = _get_item_or_404(request.POST["code"])
    receipt_id = request.session["receipt"]
    receipt = get_object_or_404(Receipt, pk=receipt_id)

    if item.state == Item.BROUGHT:
        item.state = Item.STAGED
        item.save()

        ReceiptItem.objects.create(item=item, receipt=receipt)
        # receipt.items.create(item=item)
        receipt.calculate_total()
        receipt.save()

        ret = item.as_dict()
        ret.update(total=receipt.total_cents)
        return ret

    else:
        # Errors.
        if item.state == Item.STAGED:
            # Staged somewhere other?
            code = RET_LOCKED

            # Should be either 0 or 1 items long.
            rec_list = []
            r_items = ReceiptItem.objects.filter(action=ReceiptItem.ADD, item__id=item.pk)
            for ri in r_items:
                rec_list.append(ri.receipt.as_dict())

        else:
            # Not in expected state.
            code = RET_CONFLICT
            rec_list = None

        # Price removed for "safety".
        ret = item.as_dict()
        ret.update(price=None, receipts=rec_list)
        return code, ret


@require_POST
@ajax_request
@require_clerk
def release_item_from_receipt(request, clerk):
    item = _get_item_or_404(request.POST["code"])
    receipt_id = request.session["receipt"]
    receipt = get_object_or_404(Receipt, pk=receipt_id)

    last_added_item = ReceiptItem.objects\
        .filter(receipt=receipt, item=item, action=ReceiptItem.ADD)\
        .order_by("-add_time")

    if len(last_added_item) == 0:
        return RET_CONFLICT, _i(u"Item is not added to receipt.")
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


@require_POST
@ajax_request
@require_clerk
def finish_receipt(request, clerk):
    receipt_id = request.session["receipt"]
    receipt = get_object_or_404(Receipt, pk=receipt_id)

    receipt.sell_time = now()
    receipt.status = Receipt.FINISHED
    receipt.save()

    Item.objects.filter(receipt=receipt, receiptitem__action=ReceiptItem.ADD).update(state=Item.SOLD)

    del request.session["receipt"]
    return receipt.as_dict()
