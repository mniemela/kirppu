# Allow  -2  -2.0  -2,0  2  2.0  2,0  and likes.
NUM_PAT = /^-?\d+([,\.]\d*)?$/

# Test if given string is a number, or convertible to one.
#
# @param str [String] Value to test.
# @return [Boolean] True if string represents a number. False otherwise.
Number.isConvertible = (str) ->
  return NUM_PAT.test(str)
