class @CounterMode extends ItemCheckoutMode

  constructor: (args...) ->
    super(args...)
    @_receipt = null


  title: -> "Checkout"
  subtitle: -> "#{@cfg.settings.clerkName} @ #{@cfg.settings.counterName}"

  actions: -> [
    [@cfg.settings.abortPrefix,       @onAbortReceipt]
    [@cfg.settings.logoutPrefix,      @onLogout]
    [@cfg.settings.payPrefix,         @onPayReceipt]
    [@cfg.settings.removeItemPrefix,  @onRemoveItem]
    ["",                              @onAddItem]
  ]

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

  onAddItem: (code) =>
    if code.trim() == "" then return

    if not @_receipt?
      @startReceipt(code)
    else
      @reserveItem(code)

  startReceipt: (code) ->
    @_receipt =
      rowCount: 0
      total: 0
      data: null

    # Changes to other modes now would result in fatal errors.
    @switcher.setMenuEnabled(false)

    Api.startReceipt(
      onResultSuccess: (data) =>
        @_receipt.data = data
        @cfg.uiRef.receiptResult.empty()
        @reserveItem(code)

      onResultError: (jqHXR) =>
        alert("Could not start receipt!")
        # Rollback.
        @_receipt = null
        @switcher.setMenuEnabled(true)
        return true
    )

  reserveItem: (code) ->
      Api.reserveItem(code,
        onResultSuccess: (data) =>
          @addRow(data.code, data.name, data.price)
          @_receipt.total += data.price

        onResultError: () =>
          alert("Could not find item: " + code)
          return true
      )

  onRemoveItem: (code) =>
    unless @_receipt? then return

    Api.releaseItem(code,
      onResultSuccess: (data) =>
        @addRow(data.code, data.name, -data.price)
        @_receipt.total -= data.price

      onResultError: () =>
        alert("Item not found on receipt: " + code)
        return true
    )

  onPayReceipt: (input) =>
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
        # Mode switching is safe to use again.
        @switcher.setMenuEnabled(true)

      onResultError: () =>
        alert("Error ending receipt!")
        return true
    )

  onAbortReceipt: =>
    unless @_receipt? then return

    Api.abortReceipt(
      onResultSuccess: (data) =>
        @_receipt.data = data
        console.log(@_receipt)
        @_receipt = null

        @addRow(null, "Aborted", null).addClass("danger")
        # Mode switching is safe to use again.
        @switcher.setMenuEnabled(true)

      onResultError: () =>
        alert("Error ending receipt!")
        return true
    )

  onLogout: =>
    if @_receipt?
      alert("Cannot logout while receipt is active!")
      return

    Api.clerkLogout(
      onResultSuccess: () =>
        console.log("Logged out #{ @cfg.settings.clerkName }.")
        @cfg.settings.clerkName = null
        @switcher.switchTo(ClerkLoginMode)

      onResultError: () =>
        alert("Logout failed!")
        return true
    )

@ModeSwitcher.registerEntryPoint("customer_checkout", CounterMode)
