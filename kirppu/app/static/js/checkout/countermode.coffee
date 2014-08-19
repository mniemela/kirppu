class @CounterMode extends ItemCheckoutMode

  constructor: (args...) ->
    super(args...)
    @_remove_prefix = @cfg.settings.removeItemPrefix
    @_pay_prefix = @cfg.settings.payPrefix
    @_receipt = null

  title: -> "Checkout"
  subtitle: -> "#{@cfg.settings.clerkName} @ #{@cfg.settings.counterName}"
  initialMenuEnabled: true

  addRow: (code, item, price, rounded=false) ->
    if code?
      @_receipt.rowCount++
      index = @_receipt.rowCount
      if price? and price < 0 then index = -index
    else
      code = ""
      index = ""

    row = @createRow(index, code, item, price, rounded)
    @cfg.uiRef.receiptResult.prepend(row)
    return row

  onFormSubmit: (input) ->
    if input.trim() == "" then return true
    if input == @cfg.settings.logoutPrefix
      @onLogout()
      return true
    if input.indexOf(@_remove_prefix) == 0
      @onRemoveItem(input.slice(@_remove_prefix.length))
      return true
    if input.indexOf(@_pay_prefix) == 0
      @onPayReceipt(input.slice(@_pay_prefix.length))
      return true
    if input == @cfg.settings.abortPrefix
      @onAbortReceipt()
      return true

    if not @_receipt?
      @_receipt =
        rowCount: 0
        total: 0
        data: null

      # Disable menu now as changes to other modes will result fatal errors.
      @switcher.setMenuEnabled(false)

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

    row.addClass("success") for row in [
      @addRow(null, "Subtotal", @_receipt.total, true),
      @addRow(null, "Cash", input),
      @addRow(null, "Return", input - @_receipt.total, true),
    ]

    Api.finishReceipt(
      onResultSuccess: (data) =>
        @_receipt.data = data
        console.log(@_receipt)
        @_receipt = null

        # Re-enable menu. It is safe again to use.
        @switcher.setMenuEnabled(true)
      onResultError: () =>
        alert("Error ending receipt!")
        return true
    )

  onAbortReceipt: ->
    unless @_receipt? then return

    @addRow(null, "Aborted", null).addClass("danger")

    Api.abortReceipt(
      onResultSuccess: (data) =>
        @_receipt.data = data
        console.log(@_receipt)
        @_receipt = null

        @switcher.setMenuEnabled(true)

      onResultError: () =>
        alert("Error ending receipt!")
        return true
    )

  onLogout: ->
    if @_receipt?
      alert("Cannot logout while receipt is active!")
      return

    Api.clerkLogout(
      onResultSuccess: () =>
        console.log("Logged out #{ @cfg.settings.clerkName }.")
        @cfg.settings.clerkName = null
        @switchTo(ClerkLoginMode)
      onResultError: () =>
        alert("Logout failed!")
        return true
    )

@ModeSwitcher.registerEntryPoint("customer_checkout", CounterMode)
