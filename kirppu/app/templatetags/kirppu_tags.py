from kirppu.app.utils import PixelWriter
import barcode


from django import template
register = template.Library()
import base64
from cStringIO import StringIO


@register.simple_tag
def barcode_dataurl(code, ext):
    if not code or code == 'X':
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
