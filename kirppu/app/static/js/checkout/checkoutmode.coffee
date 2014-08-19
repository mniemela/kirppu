# Base class for operation modes.
#
# @abstract
class @CheckoutMode
  # @param config [Config, optional] Configuration instance override.
  constructor: (switcher, config) ->
    @cfg = if config then config else CheckoutConfig
    @uiEnabled =
      receipt: false
    @switcher = switcher

  # Switch to new mode.
  #
  # @param mode [CheckoutMode, class] Class of new mode.
  switchTo: (mode) -> @switcher.switchTo(mode)

  # Title to display in this mode.
  #
  # @return [String] Title string.
  title: -> "[unknown mode]"

  # Subtitle to display in this mode.
  #
  # @return [String, null] Subtitle string, if needed.
  subtitle: -> null

  # Value for initial state of mode switching menu.
  # * If true, menu will be enabled upon entering this mode.
  # * If false, menu will be disabled upon entering this mode.
  # * If null, nothing will be done upon entering this mode.
  initialMenuEnabled: null

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
    @cfg.uiRef.subtitleText.text(@subtitle() or "")
    if @initialMenuEnabled?
      @switcher.setMenuEnabled(@initialMenuEnabled)
    return

  # Called just befor unbind is going to be called.
  #
  # @return [Boolean] If false, this mode will not be unbound or stopped.
  onPreUnBind: -> true

  unbind: ->

  onFormSubmit: (input) -> return false

  # Return a list of <th> elements for the receipt.
  columns: -> return []

  # Empty the receipt and create new headers.
  clearReceipt: =>
    $("#receipt_table").empty().append(
      $("<thead>").append($("<tr>").append(@columns())),
      @cfg.uiRef.receiptResult.empty()
    )
