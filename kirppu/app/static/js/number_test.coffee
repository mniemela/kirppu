# Test if given string is a number, or convertible to one.
#
# @param str [String] Value to test.
# @return [Boolean] True if string represents a number. False otherwise.
Number.isConvertible = (str) ->
  return "" + (str - 0) == str
