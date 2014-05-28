import base64
import random
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.contrib.auth import get_user_model
import time

User = settings.AUTH_USER_MODEL


def get_chk(n, start=0, end=40):
    """
    Generate check code.

    :param n: Number to generate the check
    :type n: long
    :param start: Amount of LSB to ignore.
    :type start: int
    :param end: Amount of bits in the number.
    :type end: int
    :return: Check nibble
    :rtype: long
    """
    chk = 0
    for i in range(start, end, 4):
        nibble = (n >> i) & 0xF
        chk ^= nibble
    return chk & 0xF


def encode(ref, length=5):
    """
    Encode given number as a b32 string.

    :param ref: Number to encode
    :type ref: long
    :param length: Number of bytes to encode
    :type length: int
    :return: Base32 encoded string
    :rtype: str
    """
    part = ""
    for i in range(length):
        symbol = (ref >> (8 * i)) & 0xFF
        part += chr(int(symbol))

    # Encode the byte string in base32
    return base64.b32encode(part).rstrip("=")


def decode(data, length=5):
    """
    Decode b32 string as a number.

    :param data: Base32 encoded string.
    :type data: str
    :param length: Number of bytes in the string.
    :type length: int
    :return: The decoded number
    :rtype: long
    """
    data += "=" * int((5 - (1 + (length - 1) % 5)) * 1.5)
    parts = base64.b32decode(data)

    assert len(parts) == length

    number = 0L
    for i in range(length):
        number |= ord(parts[i]) << (i * 8)
    return number


class CommandCode(object):
    START_CLERK = 1
    END_CLERK = 3

    @classmethod
    def encode_code(cls, command, payload):
        """
        Encode 72-bit command code.
        Code is CMD:4 payload:46 CHK:4 zero:2 zero:16

        :param command: Command to encode
        :type command: int
        :param payload: Payload number
        :type payload: long
        :return:
        :rtype: str
        """
        code_part = ((command & 0xF) << 46) | payload
        chk = get_chk(code_part, end=50)
        code_part = (code_part << 4) | chk
        code_part <<= 18
        return encode(code_part, length=9)

    @classmethod
    def parse_code(cls, data):
        """
        Parse 72-bit command code.

        :param data: Command string
        :type data: str
        :return: Tuple containing CMD and payload or None with error message.
        :rtype: (int, long) | (None, unicode)
        """
        code = decode(data, length=9)

        # Check that 2+16 lowest bits are zero as required for CommandCode
        if code & ((1 << 18) - 1) != 0:
            return None, _(u"Not a CommandCode")

        code >>= 18
        chk = code & 0xF
        n_chk = get_chk(code, start=4, end=50)

        if chk != n_chk:
            return None, _(u"Checksum failure")
        code >>= 4
        payload = code & ((1 << 46) - 1)
        cmd = (code >> 46) & ((1 << 4) - 1)

        return int(cmd), payload


class Event(models.Model):
    name = models.CharField(max_length=256)
    start_date = models.DateField()
    end_date = models.DateField()
    #date_id = models.IntegerField(db_index=True)
    clerks = models.ManyToManyField(User, through="EventClerk")

    auto_index_vendor = models.IntegerField(default=0)

    def get_date_identifier(self):
        """
        Date identifier is encoded in 10 bits as mmdddyyyyy

        :rtype: int
        """
        return ((self.start_date.month % 4) << (5 + 3)) |\
               ((self.start_date.day % 8) << 5) |\
               (self.start_date.year % 32)

    def get_next_index(self):
        n = self.auto_index_vendor + 1
        self.auto_index_vendor = n
        self.save(update_fields=["auto_index_vendor"])
        return n

    def __unicode__(self):
        return self.name

    def get_clerk_code(self, clerk):
        """
        Get clerk code (to be encoded in command).
        The code is DID:10 PW:36.

        :param clerk: Clerk of the event
        :type clerk: User
        :return: Command code for the clerk or None if clerk is not assigned
            in event.
        :rtype: long | None
        """
        assert isinstance(clerk, get_user_model())

        try:
            c_object = EventClerk.objects.get(event=self, user=clerk)
        except EventClerk.DoesNotExist:
            return None

        did = self.get_date_identifier() & long((1 << 10) - 1)
        cid = c_object.get_code() & ((1 << 36) - 1)

        return (did << 36) | cid

    def parse_clerk_code(self, payload):
        """
        Get clerk (from command code).

        :param payload: Payload number from command code.
        :type payload: long
        :return: Event Clerk User or None if clerk is not assigned in
            event.
        :rtype: EventClerk | None
        """
        cid = payload & ((1 << 36) - 1)
        did = (payload >> 36) & ((1 << 10) - 1)
        if did != self.get_date_identifier():
            return None

        return EventClerk.parse_code(self, cid)


class EventClerk(models.Model):
    BITS = 36
    event = models.ForeignKey(Event)
    user = models.ForeignKey(User)
    code = models.CharField(max_length=16)

    def __init__(self, *args, **kwargs):
        super(EventClerk, self).__init__(*args, **kwargs)
        self._code = None

    #noinspection PyClassHasNoInit
    class Meta:
        unique_together = ("event", "code")

    def save(self, *args, **kwargs):
        exc = None
        for _ in range(16):
            try:
                self._ensure_code()
                super(EventClerk, self).save(*args, **kwargs)
            except EventClerk.IntegrityError, e:
                self.code = None
                exc = e
            else:
                return
        raise exc

    @classmethod
    def _gen_hex(cls, num):
        """

        :param num:
        :type num: long
        :return:
        :rtype: str
        """
        out = ""
        for i in range(0, cls.BITS, 4):
            nibble = num & 0xF
            out = "{0:X}".format(nibble) + out
            num >>= 4
        return out

    def _ensure_code(self):
        """
        Ensure that encoding code is set for the clerk.
        """
        if self.code is not None and len(self.code) > 0:
            return

        self._code = random.randint(0, (1 << self.BITS) - 1)
        self.code = self._gen_hex(self._code)

    def get_code(self):
        """
        Return long representation of the encoding code.

        :rtype: long
        """
        if self._code is not None:
            return self._code

        out = 0L
        for c in self.code[:(self.BITS / 4)]:
            out <<= 4
            out |= int(c, 16)
        self._code = out
        return out

    @classmethod
    def parse_code(cls, event, code):
        """
        Parse given code and return EventClerk its corresponding instance if existing.

        :param event: Selected event object.
        :type event: Event
        :param code: Payload from command code.
        :type code: long
        :rtype: EventClerk | None
        """
        out = cls._gen_hex(code)
        try:
            return cls.objects.get(event=event, code=out)
        except cls.DoesNotExist:
            return None


def _vendor_index_validator(value):
    if value > (2 ** 14 - 1):
        raise ValidationError(_(u"Vendor index overflow, {0}").format(value))


class Vendor(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(User)
    index = models.IntegerField(validators=[_vendor_index_validator])

    #noinspection PyClassHasNoInit
    class Meta:
        unique_together = (
            ('event', 'user'),
            ('event', 'index'),
        )

    def __unicode__(self):
        name = self.user.get_full_name()
        if len(name) == 0:
            return self.user.get_username()
        return name

    @classmethod
    def new(cls, event, user):
        """
        Construct new Vendor with automatically calculated vendor index.

        :param event: Event instance
        :type event: Event
        :param user: User instance
        :type user: User
        :return: Vendor
        """
        while True:
            try:
                n = event.get_next_index()
                obj = cls(event=event, user=user, index=n)
                obj.save()
            except Vendor.IntegrityError:
                time.sleep(random.uniform(0, 0.5))
                event = Event.objects.get(pk=event.pk)
            else:
                return obj


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

    event = models.ForeignKey(Event)
    code = models.CharField(max_length=16, blank=True, null=False, db_index=True,
                            help_text=_(u"Barcode content of the product"))

    name = models.CharField(max_length=256)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    vendor = models.ForeignKey(Vendor)
    state = models.CharField(choices=STATE, max_length=8, default=ADVERTISED)

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

    @staticmethod
    def _swap(number, i1, i2):
        """
        Swap given bits from number.

        :param number: A number
        :type number: int or long
        :param i1: Bit index
        :type i1: int
        :param i2: Bit index
        :type i2: int
        :return: A number with given bits swapped.
        :rtype: int or long
        """
        b1 = (1 << i1)
        b2 = (1 << i2)
        v1 = number & b1
        v2 = number & b2

        if v1 and v2 or not (v1 or v2):
            return number
        if v1:
            number ^= b1
            number |= b2
        else:
            number |= b1
            number ^= b2
        return number

    def gen_barcode(self):
        """
        Generate bar code data. Format of the data in 40bits is
        SID:12 DID:10 PID:14 CHK:4

        :return: Bar code data.
        :rtype str
        """

        # Filter values to correct bit amounts
        did = self.event.get_date_identifier() & long((1 << 10) - 1)
        sid = self.vendor.index & long((1 << 12) - 1)
        pid = self.pk & long((1 << 14) - 1)  # FIXME: This will overflow at 16k, consider event-based index

        # Merge the values to specified format
        ref = sid << (10 + 14 + 4) | did << (14 + 4) | (pid << 4)

        ref |= get_chk(ref)

        # Encode the merged number as binary 5-byte string
        return encode(ref)

    @staticmethod
    def parse_barcode(data):
        """
        Parse bar code data.

        :param data: bar code data scanned from product.
        :type data: str
        :return: A tuple containing DateID, VendorID, ProductID, Checksum check
            result.
        :rtype: (int, int, int, bool)
        """

        number = decode(data)
        n_chk = get_chk(number, start=4)

        chk = number & 0xF
        pid = (number >> 4) & ((1 << 14) - 1)
        did = (number >> (14 + 4)) & ((1 << 10) - 1)
        sid = (number >> (10 + 14 + 4)) & ((1 << 12) - 1)

        return did, sid, pid, chk == n_chk

    @staticmethod
    def get_item_by_barcode(data):
        """
        Get Item by barcode. If code check fails, returns None.

        :param data: Bar code data scanned from product
        :type data: str
        :rtype: Item | None
        :raise Item.DoesNotExist: Raised if Item matching the code does not
            exist.
        """
        did, sid, pid, chk = Item.parse_barcode(data)

        if not chk:
            return None

        return Item.objects.get(code=data, vendor__index=sid)


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

    event = models.ForeignKey(Event)
    items = models.ManyToManyField(Item, through=ReceiptItem)
    status = models.CharField(choices=STATUS, max_length=16)
    total = models.DecimalField(max_digits=8, decimal_places=2)
    clerk = models.ForeignKey(User)
    sell_time = models.DateTimeField(null=True)
