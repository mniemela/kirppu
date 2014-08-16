class Config
  urls:
    apiValidateCounter: null
    apiClerkLogin: null
    apiClerkLogout: null
    apiItemInfo: null
    apiItemReserve: null
    apiItemRelease: null
    apiReceiptStart: null
    apiReceiptFinish: null
  uiId:
    stateText: null
    subtitleText: null
    codeInput: null
    codeForm: null
    receiptResult: null
    modeMenu: null
  uiRef:
    stateText: null
    subtitleText: null
    codeInput: null
    codeForm: null
    receiptResult: null
    modeMenu: null
  settings:
    itemPrefix: null
    clerkPrefix: "::"
    counterPrefix: ":*"
    commandPrefix: ":="
    removeItemPrefix: "-"
    payPrefix: "+"
    counterCode: null
    clerkName: null
  app:
    switcher: null

  # Check existence of uiId values and bind their references to uiRef.
  # @return True if errors. False if all ok.
  check: ->
    errors = false
    for key, value of @uiId
      element = $("#" + value)
      unless element? and element.length == 1
        console.error("Name #{value} does not identify an element for #{key}.")
        errors = true
        continue
      @uiRef[key] = element
    return errors

# Escape given string so that it can be fed literally to regular expression matching.
#
# @param txt [String] String to escape.
# @return [String] Escaped string.
escapeRegEx = (txt) ->
  # This exp matches all special characters of regular expression string.
  replacer = /([\.\[\]\(\)\{\}\*\+\?\^\$\|\\])/g;

  # This effectively escapes all previously defined characters so that they are matched
  # literally in the expression.
  return txt.replace(replacer, "\\$1")
window.escapeRegEx = escapeRegEx

window.CheckoutConfig = new Config()

# Test if given prefix is found in left hand side string.
# Can be considered to be similar to "lhs".startswith(prefix) found in some languages.
#
# @param lhs [String] Left hand side, the string to test.
# @param prefix [String] Prefix that may exist in lhs.
# @return [Boolean] True if prefix begins lhs. False if not.
hasPrefix = (lhs, prefix) ->
  return prefix? and lhs.substr(0, prefix.length) == prefix


# Functions for calling backend API. Not intended to be instantiated.
class Api
  @C = CheckoutConfig

  # Select correct success callback type for argument.
  #
  # @param fn [dict, class, function, null] If dict/class instance, "onResultSuccess" will be called
  #   with same arguments as the success function of jQuery. If function, it will be called instead.
  #   If null, data from the response will be dumped to console.
  # @return [function] Callable that can be passed to ajax request success callback.
  @_sel = (fn) ->
    if fn? and "onResultSuccess" of fn
      return (data, textStatus, jqXHR) ->
        #noinspection JSCheckFunctionSignatures
        fn.onResultSuccess(data, textStatus, jqXHR)
    return if fn? then fn else (data) ->
      console.log(data)

  # Select correct error callback type for argument.
  #
  # @param fn [dict, class, null] If dict/class instance, "onResultError" will be called
  #   with same arguments as the success function of jQuery. If null, response status, content, text status
  #   and http error are dumped to console.
  # @return [function] Callable that can be passed to ajax request error callback.
  @_err = (fn) ->
    return (jqXHR, textStatus, httpError) ->
      if fn? and "onResultError" of fn
        if not fn.onResultError(jqXHR, textStatus, httpError)
          return

      console.log([
        jqXHR.status,
        if jqXHR.responseJSON? then jqXHR.responseJSON else jqXHR.responseText,
        textStatus,
        httpError,
      ])
      return

  # Validate counter code.
  #
  # @param code [String] Counter code (without prefix) to be validated.
  # @param onComplete [dict, class, function, optional] Completion function.
  @validateCounter = (code, onComplete) ->
    $.post(@C.urls.apiValidateCounter, code: code, @_sel(onComplete))
      .error(@_err(onComplete))

  # Login clerk.
  #
  # @param code [String] Clerk code (with prefix) to validate.
  # @param counter [String] Counter code (without prefix) of this counter (previously validated with validateCounter).
  # @param onComplete [dict, class, function, optional] Completion function.
  @clerkLogin = (code, counter, onComplete) ->
    args =
      code: code
      counter: counter
    $.post(@C.urls.apiClerkLogin, args, @_sel(onComplete))
      .error(@_err(onComplete))

  # Logout clerk.
  #
  # @param onComplete [dict, class, function, optional] Completion function.
  @clerkLogout = (onComplete) ->
    $.post(@C.urls.apiClerkLogout, @_sel(onComplete))
      .error(@_err(onComplete))

  # Find item with item code.
  #
  # @param code [String] Item code to find.
  # @param onComplete [dict, class, function, optional] Completion function.
  @findItem = (code, onComplete) ->
    $.get(@C.urls.apiItemInfo, code: code, @_sel(onComplete))
      .error(@_err(onComplete))

  # Start new receipt.
  #
  # @param onComplete [dict, class, function, optional] Completion function.
  @startReceipt = (onComplete) ->
    $.post(@C.urls.apiReceiptStart, @_sel(onComplete))
      .error(@_err(onComplete))

  # Reserve given item for current receipt.
  #
  # @param itemCode [String] Item code.
  # @param onComplete [dict, class, function, optional] Completion function.
  @reserveItem = (itemCode, onComplete) ->
    $.post(@C.urls.apiItemReserve, code: itemCode, @_sel(onComplete))
      .error(@_err(onComplete))

  @releaseItem = (itemCode, onComplete) ->
    $.post(@C.urls.apiItemRelease, code: itemCode, @_sel(onComplete))
      .error(@_err(onComplete))

  # Finish currently active receipt.
  #
  # @param onComplete [dict, class, function, optional] Completion function.
  @finishReceipt = (onComplete) ->
    $.post(@C.urls.apiReceiptFinish, @_sel(onComplete))
      .error(@_err(onComplete))

window.Api = Api


#region Cents conversion functions

# Length of digits in fraction part. Leave as 2 for cents representation.
Number.FRACTION_LEN = 2

# Magnitude of fraction part. Automatically calculated. (100 if FRACTION_LEN is 2.)
Number.FRACTION = 10 ** Number.FRACTION_LEN

# Format the fixed number contained to a "price".
# @return [String] Formatted price.
# @note This does not work correctly for floating point numbers.
Number.prototype.formatCents = () ->
  # Separate wholes and fractions from the cents.
  wholes = Math.floor(Math.abs(this / Number.FRACTION))
  fraction = Math.abs(this % Number.FRACTION)

  # Add prefix-zeros to the fraction part, so 2 becomes ".02" and 20 becomes ".20".
  fraction_str = ""
  fraction_len = ("" + fraction).length
  for ignored in [fraction_len...Number.FRACTION_LEN]
    fraction_str += "0"

  # Add the actual fraction after the prefix-zeros.
  fraction_str += fraction

  # Adjust sign and create output.
  if this < 0 then wholes = "-" + wholes
  return wholes + "." + fraction_str

# Parse "price" tag to cents, ie. integer.
# @return [Number] Parsed integer or null on error.
String.prototype.parseCents = () ->
  # Match the string to parts: sign, wholes, fraction
  pat = /^(-?)(\d*)(?:[,.](\d*))?$/
  matcher = pat.exec(this)
  if not matcher? then return null

  # Ensure that values are defined.
  matcher[1] = "" unless matcher[1]?
  matcher[2] = "0" unless matcher[2]?
  matcher[3] = "0" unless matcher[3]?

  # Convert to integer.
  wholes = matcher[2] - 0
  fraction = matcher[3] - 0

  # Adjust fraction so that ".2" equals 20 and ".02" equals 2.
  fraction_exp = 10 ** (Number.FRACTION_LEN - matcher[3].length)
  fraction = Math.round(fraction * fraction_exp)

  # 100 cents per a whole. (or whatever the FRACTION has been defined)
  cents = wholes * Number.FRACTION

  # Adjust by sign, and add the fraction part to cents.
  if matcher[1] != "-"
    cents += fraction
  else
    cents = -cents - fraction

  return cents

#endregion
