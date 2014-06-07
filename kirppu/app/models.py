from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth import get_user_model

from ..util import b32_encode, b32_decode, pack, unpack, InvalidChecksum

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
        :type payload: long

        :return: Encoded command code
        :rtype: str

        :raise OverflowError: If the command or payload is too large.
        """
        return b32_encode(
            pack([
                ( 4L, command),
                (46L, payload),
                (18L, 0L),
            ], check_len=4),
            length=9
        )

    @classmethod
    def parse_code(cls, data):
        """
        Parse a 72-bit command code.

        :param data: Command string
        :type data: str
        :return: Command and payload
        :rtype: (int, long)

        :raise ValueError: If the data is not valid.
        :raise InvalidChecksum: If the checksum does not match.
        """
        command, payload, zeros = unpack(
            b32_decode(data, length=9),
            [4L, 46L, 18L],
            check_len=4,
        )

        if zeros != 0L:
            raise ValueError('not a CommandCode')

        return int(cmd), payload


class Clerk(models.Model):
    user = models.ForeignKey(User)

    def __unicode__(self):
        return u'<Clerk: {0}>'.format(unicode(self.user))

    def get_code(self):
        return number_to_hex(self.id)

    @classmethod
    def by_hex_code(cls, hex_code):
        """
        Return the Clerk instance with the given hex code.

        :param code: Hex code to look for
        :type code: str
        :return: The corresponding Clerk
        :rtype: Clerk | None
        """
        return cls.objects.get(id=hex_to_number(hex_code))


class Vendor(models.Model):
    user = models.ForeignKey(User)

    def __unicode__(self):
        return u'<Vendor: {0}>'.format(unicode(self.user))


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

    def __unicode__(self):
        return self.name

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
                (12L, self.vendor.id),
                (24L, self.pk),
            ], check_len=4)
        )

    @staticmethod
    def parse_barcode(data):
        """
        Parse barcode data into vendor id and item id.

        :param data: Barcode data scanned from product
        :type data: str
        :return: Vendor id and item id
        :rtype: (long, long)
        :raise InvalidChecksum: If the checksum does not match the data.
        """
        return unpack(
            b32_decode(data),
            [12L, 24L],
            check_len=4,
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
            _, vendor_id, _ = Item.parse_barcode(data)
        except InvalidChecksum:
            return None
        return Item.objects.get(code=data, vendor__id=vendor_id)


class ReceiptItem(models.Model):
    ADD = "ADD"
    REMOVE = "DEL"

    ACTION = (
        (ADD, _(u"Added to receipt")),
        (REMOVE, _(u"Removed from receipt")),
    )

    item = models.ForeignKey(Item)
    receipt = models.ForeignKey("Receipt")
    action = models.CharField(choices=ACTION, max_length=16, default=ADD)


class Receipt(models.Model):
    PENDING = "PEND"
    FINISHED = "FINI"

    STATUS = (
        (PENDING, _(u"Not finished")),
        (FINISHED, _(u"Finished")),
    )

    items = models.ManyToManyField(Item, through=ReceiptItem)
    status = models.CharField(choices=STATUS, max_length=16)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    clerk = models.ForeignKey(Clerk)
    sell_time = models.DateTimeField(null=True)
