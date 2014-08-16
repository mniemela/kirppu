
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

# Class for handling switching Modes from one to other.
class ModeSwitcher

  # @param config [Config, optional] Configuration instance override.
  constructor: (config) ->
    @cfg = if config then config else CheckoutConfig
    @_currentMode = null

  # Start default mode operation.
  startDefault: ->
    @switchTo(CounterValidationMode)

  # Switch to new mode. This is called by modes.
  #
  # @param mode [CheckoutMode, class] Class of new mode.
  switchTo: (mode) ->
    if @_currentMode?
      @_currentMode.unbind()
      @_currentMode = null
    newMode = new mode(@cfg)
    newMode.assignSwitcher(@)
    if not newMode.onPreBind()
      return
    newMode.bind()
    @_currentMode = newMode
    return

  # Get name of currently active mode.
  #
  # @return [String] Mode name.
  currentMode: -> if @_currentMode? then @_currentMode.constructor.name else null
window.ModeSwitcher = ModeSwitcher


# Base class for operation modes.
#
# @abstract
class CheckoutMode

  # @param config [Config, optional] Configuration instance override.
  constructor: (config) ->
    @cfg = if config then config else CheckoutConfig
    @uiEnabled =
      receipt: false
    @switcher = null

  # Assign mode switcher for the mode.
  #
  # @param switcher [ModeSwitcher] ModeSwitcher instance.
  assignSwitcher: (switcher) ->
    @switcher = switcher

  # Switch to new mode.
  #
  # @param mode [CheckoutMode, class] Class of new mode.
  switchTo: (mode) ->
    if not @switcher?
      console.log("Would switch mode to " + mode)
      return

    @switcher.switchTo(mode)

  # Title to display in this mode.
  #
  # @return [String] Title string.
  title: -> "[unknown mode]"

  # Subtitle to display in this mode.
  #
  # @return [String, null] Subtitle string, if needed.
  subtitle: -> null

  # Called just before bind is going to be called.
  #
  # @return [Boolean] If false, this mode will not be bound or activated. It will also not be unbound.
  onPreBind: -> true

  # Bind functions to HTML elements.
  #
  # @param form [$, optional] Form jQuery reference.
  # @param input [$, optional] Input field jQuery reference.
  bind: (form, input) ->
    form = @cfg.uiRef.codeForm unless form?
    input = @cfg.uiRef.codeInput unless input?
    form.off("submit")
    form.submit((event) =>
      value = input.val()
      ret = @onFormSubmit(value)
      if ret
        input.val("")
      else
        console.error("Input not accepted: '#{value}', ret=#{ret}, this=#{@.constructor.name}")
      event.preventDefault()
    )
    @cfg.uiRef.stateText.text(@title())
    subtitle = @subtitle()
    if subtitle?
      @cfg.uiRef.stateText.append(" ", $("<small>").text(subtitle))
    return

  unbind: ->

  onFormSubmit: (input) ->
    return false

window.CheckoutMode = CheckoutMode


# Create RegExp that will match content after given prefix.
#
# @param prefix [String] Plaintext prefix.
# @return [RegExp] Regular expression instance.
contentAfterPrefixRe = (prefix) ->
  return new RegExp("^" + escapeRegEx(prefix) + "(.+)$")


class CounterValidationMode extends CheckoutMode
  @COOKIE = "mCV"

  constructor: (config) ->
    super(config)
    @_prefix = contentAfterPrefixRe(@cfg.settings.counterPrefix)

  title: -> "Locked"
  subtitle: -> "Need to validate counter."

  onPreBind: ->
    # If we have values for Counter in cookie storage, use them and don't start this mode at all.
    code = $.cookie(@constructor.COOKIE)
    if code?
      data = JSON.parse(b64_to_utf8(code))
      @onResultSuccess(data)
      return false
    super()

  onFormSubmit: (input) ->
    parsed = @_prefix.exec(input)
    if not parsed?
      return false
    code = parsed[1]  # Code without prefix.

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


class ClerkLoginMode extends CheckoutMode
  constructor: (config) ->
    super(config)
    @_prefix = contentAfterPrefixRe(@cfg.settings.clerkPrefix)

  title: -> "Locked"
  subtitle: -> "Login..."

  onFormSubmit: (input) ->
    parsed = @_prefix.exec(input)
    if not parsed?
      return false
    code = parsed[0]  # Code with prefix.
    counter = @cfg.settings.counterCode
    Api.clerkLogin(code, counter, @)

  onResultSuccess: (data) ->
    username = data["user"]
    @cfg.settings.clerkName = username
    console.log("Logged in as #{username}.")
    @switchTo(CounterMode)

  onResultError: (jqXHR) ->
    if jqXHR.status == 419
      console.log("Login failed: " + jqXHR.responseJSON["message"])
      return
    return true


class ItemFindMode extends CheckoutMode
  constructor: (config) ->
    super(config)

  title: -> "Find"
  subtitle: -> "#{@cfg.settings.clerkName} @ #{@cfg.settings.counterName}"

  onFormSubmit: (input) ->
    Api.findItem(input, @)

  onResultSuccess: (data) ->
    row = createRow("?", data.code, data.name, data.price)
    @cfg.uiRef.receiptResult.append(row)

  onResultError: (jqXHR) ->
    if jqXHR.status == 404
      alert("No such item")
      return
    return true


# Helper function to create a row in receipt table.
# All arguments are used for display-only.
#
# @param index [Integer] Index of the item.
# @param code [String] Item code.
# @param name [String] Item name.
# @param price [Integer, optional] Price of the item in cents.
# @param rounded [Boolean, optional] Should the price be displayed also as rounded?
# @return [$] Table row (tr element) as jQuery object.
createRow = (index, code, name, price=null, rounded=false) ->
  row = $("<tr>")
  price_str = if price? then price.formatCents() + "€" else ""
  if rounded
    modulo = price % 5
    if modulo >= 3
      rounded_value = price + (5 - modulo)
    else
      rounded_value = price - modulo
    rounded_str = rounded_value.formatCents() + "€"
    price_str = "#{ rounded_str } (#{ price_str })"

  row.append(
    $("<td>").text(index),
    $("<td>").text(code),
    $("<td>").text(name),
    $("<td>").text(price_str)
  )
  return row


class CounterMode extends CheckoutMode
  constructor: (config) ->
    super(config)
    @_p_remove = contentAfterPrefixRe(@cfg.settings.removeItemPrefix)
    @_p_pay = contentAfterPrefixRe(@cfg.settings.payPrefix)
    @_receipt = null

  title: -> "Checkout"
  subtitle: -> "#{@cfg.settings.clerkName} @ #{@cfg.settings.counterName}"

  addRow: (code, item, price, rounded=false) ->
    if code?
      @_receipt.rowCount++
      index = @_receipt.rowCount
      if price? and price < 0 then index = -index
    else
      code = ""
      index = ""

    row = createRow(index, code, item, price, rounded)
    @cfg.uiRef.receiptResult.prepend(row)
    return row

  onFormSubmit: (input) ->
    if input.trim() == "" then return true
    if @tryPattern(@_p_remove, input, @onRemoveItem) then return true
    if @tryPattern(@_p_pay, input, @onPayReceipt) then return true

    if not @_receipt?
      @_receipt =
        rowCount: 0
        total: 0
        data: null

      Api.startReceipt(
        onResultSuccess: (data) =>
          @_receipt.data = data
          @cfg.uiRef.receiptResult.empty()
          @onFormSubmit(input)
        onResultError: (jqHXR) =>
          alert("Could not start receipt!")
          return true
      )
      return true

    Api.reserveItem(input,
      onResultSuccess: (data) =>
        @addRow(data.code, data.name, data.price)
        @_receipt.total += data.price

      onResultError: () =>
        alert("Could not find item: " + input)
        return true
    )

    return true


  tryPattern: (pattern, input, fn) ->
    value = pattern.exec(input)
    if value?
      fn.call(@, value[1])
      return true
    return false

  onRemoveItem: (input) ->
    unless @_receipt? then return

    Api.releaseItem(input,
      onResultSuccess: (data) =>
        @addRow(data.code, data.name, -data.price)
        @_receipt.total -= data.price

      onResultError: () =>
        alert("Item not found on receipt: " + input)
        return true
    )

  onPayReceipt: (input) ->
    unless @_receipt? then return
    input = input - 0

    if input < @_receipt.total
      alert("Not enough given money!")
      return

    @addRow(null, "Subtotal", @_receipt.total, true)
    @addRow(null, "Cash", input)
    @addRow(null, "Return", input - @_receipt.total, true)

    Api.finishReceipt(
      onResultSuccess: (data) =>
        @_receipt.data = data
        console.log(@_receipt)
        @_receipt = null
      onResultError: () =>
        alert("Error ending receipt!")
        return true
    )



window.CounterValidationMode = CounterValidationMode
window.ClerkLoginMode = ClerkLoginMode
window.ItemFindMode = ItemFindMode
