class Config
  urls:
    apiValidateCounter: null
    apiClerkLogin: null
    apiClerkLogout: null
    apiItemInfo: null
    apiItemReserve: null
    apiReceiptStart: null
    apiReceiptFinish: null
  uiId:
    stateText: null
    codeInput: null
    codeForm: null
    receiptResult: null
  uiRef:
    stateText: null
    codeInput: null
    codeForm: null
    receiptResult: null
  settings:
    itemPrefix: null
    clerkPrefix: "::"
    counterPrefix: ":*"
    commandPrefix: ":="
    removeItemPrefix: "-"
    payPrefix: "+"
  app:
    inputHandler: null

  check: ->
    errors = false
    for key, value of @uiId
      element = $("#" + value)
      unless element? and element.length == 1
        console.error("Name #{value} does not identify an element for #{key}.")
        errors = true
        continue
      @uiRef[key] = element
    errors = @_bind() unless errors
    return errors

  _bind: ->
    if @app.inputHandler?
      @app.inputHandler.bind()
    return false


window.CheckoutConfig = new Config()

class State
  constructor: ->
    @counterInfo = null
    @clerkInfo = null

  canLoginClerk: ->
    return @counterInfo?

  canValidateCounter: ->
    return not @counterInfo?

  canStartReceipt: ->
    return @counterInfo? and @clerkInfo

  getHeadingText: ->
    return "Checkout "


class InputHandler
  constructor: (config) ->
    @cfg = if config then config else CheckoutConfig
    @enabled =
      clerk: true
      counter: true
      command: true
      item: true

  bind: ->
    @cfg.uiRef.codeForm.submit((event) =>
      ctl = @cfg.uiRef.codeInput
      value = ctl.val()
      ret = @onInput(value)
      if ret is true
        ctl.val("")
      else
        console.error("Input not understood: '#{value}', ret=#{ret}")
      event.preventDefault()
    )

  onInput: (input) ->
    settings = @cfg.settings

    if hasPrefix(input, settings.clerkPrefix)
      @onInputClerk(input)

    else if hasPrefix(input, settings.counterPrefix)
      @onInputCounter(input)

    else if hasPrefix(input, settings.commandPrefix)
      @onInputCommand(input)

    else if not settings.itemPrefix? or hasPrefix(input, settings.itemPrefix)
      @onInputItem(input)

    else
      return false
    return true

  onInputClerk: (input) ->

  onInputCounter: (input) ->

  onInputCommand: (input) ->

  onInputItem: (input) ->
    Api.findItem(input, (data) =>
      row = $("<tr>")
      row.append(
        $("<td>").text("?"),
        $("<td>").text(data.code),
        $("<td>").text(data.name),
        $("<td>").text(data.price.formatCents())
      )

      @cfg.uiRef.receiptResult.append(row)
    )
window.InputHandler = InputHandler

hasPrefix = (lhs, prefix) ->
  return prefix? and lhs.substr(0, prefix.length) == prefix

class Api
  @C = CheckoutConfig

  @_dump = (data) ->
    console.log(JSON.stringify(data))

  @_sel = (fn) ->
    return if fn? then fn else @_dump

  @validateCounter = (code, onComplete) ->
    $.post(@C.urls.apiValidateCounter, code: code, @_sel(onComplete))

  @clerkLogin = (code, counter, onComplete) ->
    args =
      code: code
      counter: counter
    $.post(@C.urls.apiClerkLogin, args, @_sel(onComplete))

  @clerkLogout = (onComplete) ->
    $.post(@C.urls.apiClerkLogout, @_sel(onComplete))

  @findItem = (code, onComplete) ->
    $.get(@C.urls.apiItemInfo, code: code, @_sel(onComplete))

  @startReceipt = (onComplete) ->
    $.post(@C.urls.apiReceiptStart, @_sel(onComplete))

  @reserveItem = (itemCode, onComplete) ->
    $.post(@C.urls.apiItemReserve, code: itemCode, @_sel(onComplete))

  @finishReceipt = (onComplete) ->
    $.post(@C.urls.apiReceiptFinish, @_sel(onComplete))

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
  wholes = Math.abs(Math.round(this / Number.FRACTION))
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
