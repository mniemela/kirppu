import base64

"""
Miscellaneous utility functions.
"""


def swap(number, i1, i2):
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


def number_to_hex(number, width):
    """
    Return the hex string representation of the given number.
    Convert the given number to a hex string.

    :param number: Number to convert
    :type number: long

    :param width: Width of the result in bits
    :type width: long

    :return: The number as a hex string
    :rtype: str

    :raise OverflowError: If the number does not fit into the given width.
    """
    if number >> width != 0L:
        raise OverflowError(
            '{0} does not fit into {1} bits'.format(number, width)
        )
    return '{0:0{1}X}'.format(number, math.ceil(width / 4L))


def hex_to_number(hex_string):
    """
    Return a long representation of the encoding code.

    :param hex_string: Hex string to convert
    :type hex_string: str
    :return: The hex string as a number
    :type: long
    """
    return long(hex_string, 16)


def b32_encode(ref, length=5):
    """
    Encode a number as a b32 string.

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


def b32_decode(data, length=5):
    """
    Decode a b32 string as a number.

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


def pack(fields, check_len=0L):
    """
    Pack numbers into a single number.

    Each element of `fields` is a pair of numbers specifying a single data
    field. The first element specifies the width (in bits) of the field.
    The second element of the pair specifies the actual data to pack.

    :param fields: The data fields and their widths
    :type fields: [(long, long)]

    :param check_len: Length of the checksum to append
    :type check_len: long

    :return: Packed data
    :rtype: long

    :raise OverflowError: If some data does not fit into the specified width.
    """
    result = 0L

    for width, number in fields:
        if number >> width != 0L:
            raise OverflowError(
                '{0} does not fit into {1} bits'.format(number, width)
            )
        result <<= width
        result |= number

    csum = checksum(result, check_len)
    result <<= check_len
    result |= csum
    return result


class InvalidChecksum(ValueError):
    pass


def unpack(data, fields, check_len=0L):
    """
    Unpack packed data.

    Each element of `fields` specifies the width a single data field.

    :param data: Packed data
    :type data: long

    :param fields: The widths of the data fields
    :type fields: [long]

    :param check_len: Length of the checksum
    :type check_len: long

    :return: List of unpacked data fields
    :rtype: [long]

    :raise InvalidChecksum: If the checksum does not match the data.
    """
    csum = data & ((1L << check_len) - 1)
    data >>= check_len
    if csum != checksum(data, check_len):
        raise InvalidChecksum()

    result = []

    for width in reversed(fields):
        extracted = data & ((1L << width) - 1L)
        result.append(extracted)
        data >>= width
    result.reverse()
    return result


def checksum(number, length=4L):
    """
    Calculate the checksum of a number.

    The checksum of length N is formed by splitting the number into
    bitstrings of N bits and performing a bitwise exclusive or on them.

    :param number: Number to generate the check
    :type number: long

    :return: Checksum of the number
    :rtype: long
    """
    if length == 0:
        return 0

    mask = (1L << length) - 1L
    chk = 0L
    while number > 0L:
        chk ^= (number & mask)
        number >>= length
    return chk & mask
