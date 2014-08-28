from kirppu.app.utils import PixelWriter
import barcode
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


def generate_dataurl(code, ext):
    if not code:
        return ''

    writer = PixelWriter(format=ext)
    mimetype = 'image/' + ext

    # PIL only writes to
    bar = barcode.Code128(code, writer=writer)
    memory_file = StringIO()
    pil_image = bar.render({ 'module_width': 1 })
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

