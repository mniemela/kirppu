from kirppu.app.utils import PixelWriter
import barcode
from barcode.charsets import code128
from django import template
register = template.Library()
import base64
from cStringIO import StringIO
from django.utils.functional import memoize
from collections import OrderedDict


class FifoDict(OrderedDict):
    def __init__(self, *args, **kwargs):
        self.limit = kwargs.pop("limit", None)
        OrderedDict.__init__(self, *args, **kwargs)
        self._remove_oldest()

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._remove_oldest()

    def _remove_oldest(self):
        if not self.limit:
            return

        while len(self) > self.limit:
            self.popitem(last=False)


# Limit the size of the dict to a reasonable number so that we don't have
# millions of dataurls cached.
barcode_dataurl_cache = FifoDict(limit=50000)


class KirppuBarcode(barcode.Code128):
    """Make sure barcode is always the same width"""

    def _maybe_switch_charset(self, pos):
        """Do not switch ever."""
        char = self.code[pos]
        assert(char in code128.B)
        return []

    def _try_to_optimize(self, encoded):
        return encoded


def generate_dataurl(code, ext):
    if not code:
        return ''

    writer = PixelWriter(format=ext)
    mimetype = 'image/' + ext

    # PIL only writes to
    bar = KirppuBarcode(code, writer=writer)
    memory_file = StringIO()
    pil_image = bar.render({ 'module_width': 1 })

    width, height = pil_image.size

    # These measurements have to be exactly the same as the ones used in
    # price_tags.css. If they are not the image might be distorted enough
    # to not register on the scanner.
    assert(height == 1)
    assert(width == 143)

    pil_image.save(memory_file, format=ext)
    data = memory_file.getvalue()

    dataurl_format = 'data:{mimetype};base64,{base64_data}'
    return dataurl_format.format(
            mimetype=mimetype,
            base64_data=base64.encodestring(data))
get_dataurl = memoize(generate_dataurl, barcode_dataurl_cache, 2)


@register.simple_tag
def barcode_dataurl(code, ext):
    return get_dataurl(code, ext)

