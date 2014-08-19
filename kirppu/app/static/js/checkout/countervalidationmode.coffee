# Encode give Utf-8 string to base64.
#
# @param str [String] String to encode.
# @return [String] Base64 encoded string.
utf8_to_b64 = (str) ->
    return window.btoa(encodeURIComponent(escape( str )))

# Decode base64 string to Utf-8 string.
#
# @param str [String] Base64 to decode.
# @return [String] Utf-8 string.
b64_to_utf8 = (str) ->
    return unescape(decodeURIComponent(window.atob( str )))

class @CounterValidationMode extends CheckoutMode
  @COOKIE = "mCV"

  constructor: (config) ->
    super(config)
    @_prefix = @cfg.settings.counterPrefix

  title: -> "Locked"
  subtitle: -> "Need to validate counter."
  initialMenuEnabled: false

  onPreBind: ->
    # If we have values for Counter in cookie storage, use them and don't
    # start this mode at all.
    code = $.cookie(@constructor.COOKIE)
    if code?
      data = JSON.parse(b64_to_utf8(code))
      @onResultSuccess(data)
      return false
    super()

  onFormSubmit: (input) ->
    if input.indexOf(@_prefix) != 0
      return false
    code = input.slice(@_prefix.length) # Code without prefix.

    # Call backend. Results in onResult* functions.
    Api.validateCounter(code, @)

  onResultSuccess: (data) ->
    code = data["counter"]
    name = data["name"]
    @cfg.settings.counterCode = code
    @cfg.settings.counterName = name
    console.log("Validated #{code} as #{name}.")

    # Store values for next time so the mode can be skipped.
    $.cookie(@constructor.COOKIE, utf8_to_b64(JSON.stringify(
      counter: code
      name: name
    )))
    @switchTo(ClerkLoginMode)

  onResultError: (jqXHR) ->
    if jqXHR.status == 419
      console.log("Invalid counter code supplied.")
      return
    return true

  @clearStore: ->
    $.removeCookie(@COOKIE)

@ModeSwitcher.registerEntryPoint("counter_validation", CounterValidationMode)
