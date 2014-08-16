import random
from django.db import models
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth import get_user_model
from kirppu.app.utils import model_dict_fn, format_datetime

from ..util import (
    number_to_hex,
    hex_to_number,
    b32_encode,
    b32_decode,
    pack,
    unpack,
    InvalidChecksum,
)

User = settings.AUTH_USER_MODEL


class CommandCode(object):
    START_CLERK = 1
    END_CLERK = 3

    @classmethod
    def encode_code(cls, command, payload):
        """
        Encode a 72-bit command code.

        Format of the code:
            command:     4 bits
            payload:    46 bits
            zeros:      18 bits
            checksum:    4 bits
            -------------------
            total:      40 bits

        :param command: Command to encode
        :type command: int

        :param payload: Payload data
        :type payload: int

        :return: Encoded command code
        :rtype: str

        :raise OverflowError: If the command or payload is too large.

        >>> CommandCode.encode_code(
        ...     CommandCode.END_CLERK,
        ...     123456789,
        ... )
        'AAAEARPT2YAQAMA'

        """
        return b32_encode(
            pack([
                ( 4, command),
                (46, payload),
                (18, 0),
            ], checksum_bits=4),
            length=9
        )

    @classmethod
    def parse_code(cls, data):
        """
        Parse a 72-bit command code.

        :param data: Command string
        :type data: str
        :return: Command and payload
        :rtype: (int, int)

        :raise ValueError: If the data is not valid.
        :raise InvalidChecksum: If the checksum does not match.

        >>> CommandCode.parse_code('AAAEARPT2YAQAMA') == (3, 123456789)
        True
        >>> CommandCode.parse_code('7QBUARPT2YAQAMA')
        Traceback (most recent call last):
            ...
        ValueError: not a CommandCode
        >>> CommandCode.parse_code('0')
        Traceback (most recent call last):
            ...
        ValueError: not a CommandCode
        >>> CommandCode.parse_code('AAAEARPT2YARAMA')
        Traceback (most recent call last):
            ...
        InvalidChecksum

        """
        try:
            command, payload, zeros = unpack(
                b32_decode(data, length=9),
                [4, 46, 18],
                checksum_bits=4,
            )
        except TypeError:
            raise ValueError('not a CommandCode')

        if zeros != 0:
            raise ValueError('not a CommandCode')

        return int(command), payload


class Clerk(models.Model):
    PREFIX = "::"

    user = models.OneToOneField(User, null=True)    
    access_key = models.CharField(
        max_length=128,
        unique=True,
        null=True,
        blank=True,
        verbose_name=u"Access key value",
        help_text=u"Access code assigned to the clerk.")

    def __unicode__(self):
        if self.user is not None:
            return unicode(self.user)
        else:
            return u'id={0}'.format(str(self.id))

    def as_dict(self):
        return {
            "user": unicode(self.user)
        }

    def get_code(self):
        """
        Get access card code for this Clerk.

        Format of the code (without '::' prefix):
            zeros:       4 bits
            access_key: 56 bits
            checksum:    4 bits
            -------------------
            total:      64 bits

        :return: Clerk code.
        :rtype: str
        """
        access_key = hex_to_number(self.access_key)
        return self.PREFIX + b32_encode(
            pack([
                (4, 0),
                (56, access_key),
            ], checksum_bits=4),
            length=8
        )

    @property
    def access_code(self):
        if self.access_key is not None:
            return self.get_code()
        return ""

    @classmethod
    def by_code(cls, code):
        """
        Return the Clerk instance with the given hex code.
        The access card code should include prefix "::".

        :param code: Raw code string from access card.
        :type code: str
        :return: The corresponding Clerk or None if access token is invalid.
        :rtype: Clerk | None
        :raises: ValueError if not a valid Clerk access code.
        """
        prefix_len = len(cls.PREFIX)
        if len(code) <= prefix_len or code[:prefix_len] != cls.PREFIX:
            raise ValueError("Not a Clerk code")
        code = code[prefix_len:]
        try:
            zeros, access_key = unpack(
                b32_decode(code, length=8),
                [4, 56],
                checksum_bits=4,
            )
        except TypeError:
            raise ValueError("Not a Clerk code")

        if zeros != 0:
            raise ValueError("Not a Clerk code")

        access_key_hex = number_to_hex(access_key, 56)
        try:
            clerk = cls.objects.get(access_key=access_key_hex)
        except cls.DoesNotExist:
            return None
        if clerk.user is None:
            return None
        return clerk

    def generate_access_key(self):
        """
        Generate new access token for this Clerk. This will automatically overwrite old value.

        :return: The newly generated token.
        """
        key = None
        while key is None or Clerk.objects.filter(access_key=key).exists():
            key = random.randint(1, 2 ** 56 - 1)
        self.access_key = number_to_hex(key, 56)
        return key

    @classmethod
    def generate_empty_clerks(cls, count=1, commit=True):
        """
        Generate unbound Clerks, i.e. Clerks that have access-code but no user.
        These Clerks can be "moved" to existing clerks so that the real Clerk will start
        using the access key from unbound one.

        This allows access codes to be pre-populated and printed to cards, which then can be
        taken easily to use in case of need without needing to create the card then.

        :param count: Count of unbound Clerks to generate, default 1.
        :type count: int
        :return: List of generated rows.
        :rtype: list[Clerk]
        """
        ids = []
        for _ in range(count):
            item = cls()
            item.generate_access_key()
            if commit:
                item.save()
            ids.append(item)
        return ids


class Vendor(models.Model):
    user = models.OneToOneField(User)

    def __unicode__(self):
        return u'<Vendor: {0}>'.format(unicode(self.user))

    @classmethod
    def get_vendor(cls, user):
        if not hasattr(user, 'vendor'):
            vendor = cls(user=user)
            vendor.save()
        return user.vendor


class Item(models.Model):
    ADVERTISED = "AD"
    BROUGHT = "BR"
    STAGED = "ST"
    SOLD = "SO"
    MISSING = "MI"
    RETURNED = "RE"
    COMPENSATED = "CO"

    STATE = (
        (ADVERTISED, _(u"Advertised")),
        (BROUGHT, _(u"Brought to event")),
        (STAGED, _(u"Staged for selling")),
        (SOLD, _(u"Sold")),
        (MISSING, _(u"Missing")),
        (RETURNED, _(u"Returned to vendor")),
        (COMPENSATED, _(u"Compensated to vendor")),
    )

    TYPE_SHORT = "short"
    TYPE_LONG = "long"
    TYPE = (
        (TYPE_SHORT, _(u"Short price tag")),
        (TYPE_LONG, _(u"Long price tag")),
    )

    FRACTION_LEN = 2
    FRACTION = 10 ** FRACTION_LEN

    code = models.CharField(
        max_length=16,
        blank=True,
        null=False,
        db_index=True,
        help_text=_(u"Barcode content of the product"),
    )
    name = models.CharField(max_length=256)
    # FIXME: prevent negative prices
    price = models.DecimalField(max_digits=8, decimal_places=2)
    vendor = models.ForeignKey(Vendor)
    state = models.CharField(
        choices=STATE,
        max_length=8,
        default=ADVERTISED
    )
    type = models.CharField(
        choices=TYPE,
        max_length=8,
        default=TYPE_SHORT
    )

    def __unicode__(self):
        return self.name

    as_dict = model_dict_fn("code", "name", "state", price="price_cents")

    @property
    def price_cents(self):
        return long(self.price * self.FRACTION)

    @classmethod
    def new(cls, *args, **kwargs):
        """
        Construct new Item and generate its barcode.

        :param args: Item Constructor arguments
        :param kwargs: Item Constructor arguments
        :return: New stored Item object with calculated code.
        :rtype: Item
        """
        obj = cls(*args, **kwargs)
        obj.save()

        obj.code = obj.gen_barcode()
        obj.save(update_fields=["code"])
        return obj

    def gen_barcode(self):
        """
        Generate and return barcode data for the Item.

        Format of the code:
            vendor id:  12 bits
            item id:    24 bits
            checksum:    4 bits
            -------------------
            total:      40 bits

        :return: Barcode data.
        :rtype str
        """
        return b32_encode(
            pack([
                (12, self.vendor.id),
                (24, self.pk),
            ], checksum_bits=4)
        )

    @staticmethod
    def parse_barcode(data):
        """
        Parse barcode data into vendor id and item id.

        :param data: Barcode data scanned from product
        :type data: str
        :return: Vendor id and item id
        :rtype: (int, int)
        :raise InvalidChecksum: If the checksum does not match the data.
        """
        return unpack(
            b32_decode(data),
            [12, 24],
            checksum_bits=4,
        )

    @staticmethod
    def get_item_by_barcode(data):
        """
        Get Item by barcode. If code check fails, returns None.

        :param data: Barcode data scanned from product
        :type data: str

        :rtype: Item | None
        :raise Item.DoesNotExist: If no Item matches the code.
        """
        try:
            vendor_id, _ = Item.parse_barcode(data)
        except InvalidChecksum:
            return None
        return Item.objects.get(code=data, vendor__id=vendor_id)


class Counter(models.Model):
    identifier = models.CharField(
        max_length=32,
        blank=True,
        null=False,
        unique=True,
        help_text=_(u"Identifier of the counter")
    )
    name = models.CharField(
        max_length=64,
        blank=True,
        null=False,
        help_text=_(u"Name of the counter")
    )

    def __unicode__(self):
        return u"{1} ({0})".format(self.identifier, self.name)


class ReceiptItem(models.Model):
    ADD = "ADD"
    REMOVED_LATER = "RL"
    REMOVE = "DEL"

    ACTION = (
        (ADD, _(u"Added to receipt")),
        (REMOVED_LATER, _(u"Removed later")),
        (REMOVE, _(u"Removed from receipt")),
    )

    item = models.ForeignKey(Item)
    receipt = models.ForeignKey("Receipt")
    action = models.CharField(choices=ACTION, max_length=16, default=ADD)
    add_time = models.DateTimeField(auto_now_add=True)

    def as_dict(self):
        ret = {
            "action": self.action,
        }
        ret.update(self.item.as_dict())
        return ret


class Receipt(models.Model):
    PENDING = "PEND"
    FINISHED = "FINI"

    STATUS = (
        (PENDING, _(u"Not finished")),
        (FINISHED, _(u"Finished")),
    )

    items = models.ManyToManyField(Item, through=ReceiptItem)
    status = models.CharField(choices=STATUS, max_length=16, default=PENDING)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    clerk = models.ForeignKey(Clerk)
    counter = models.ForeignKey(Counter)
    start_time = models.DateTimeField(auto_now_add=True)
    sell_time = models.DateTimeField(null=True, blank=True)

    def items_list(self):
        items = []
        for item in self.items.all():
            items.append(item.as_dict())

        return items

    @property
    def total_cents(self):
        return long(self.total * Item.FRACTION)

    as_dict = model_dict_fn("status",
        total="total_cents",
        start_time=lambda self: format_datetime(self.start_time),
        sell_time=lambda self: format_datetime(self.sell_time) if self.sell_time is not None else None,
        clerk=lambda self: self.clerk.as_dict(),
        counter=lambda self: self.counter.name)

    def calculate_total(self):
        result = ReceiptItem.objects.filter(action=ReceiptItem.ADD, receipt=self)\
            .aggregate(price_total=Sum("item__price"))
        price_total = result["price_total"]
        self.total = price_total or 0
        return self.total

    def __unicode__(self):
        return unicode(self.start_time) + u" / " + unicode(self.clerk)
