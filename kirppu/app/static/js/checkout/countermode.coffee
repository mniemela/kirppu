class @CounterMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("customer_checkout", @)

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

  enter: ->
    super()
    @_setSum()

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
    if @_receipt?
      @_setSum(@_receipt.total)
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

    Api.receipt_start().then(
      (data) =>
        @_receipt.data = data
        @cfg.uiRef.receiptResult.empty()
        @_setSum()
        @reserveItem(code)

      (jqHXR) =>
        alert("Could not start receipt!")
        # Rollback.
        @_receipt = null
        @switcher.setMenuEnabled(true)
        return true
    )

  _setSum: (sum=0) ->
    @cfg.uiRef.receiptSum.text("Total: " + (sum).formatCents() + " €")

  reserveItem: (code) ->
      Api.item_reserve(code: code).then(
        (data) =>
          @_receipt.total += data.price
          @addRow(data.code, data.name, data.price)

        =>
          alert("Could not find item: " + code)
          return true
      )

  onRemoveItem: (code) =>
    unless @_receipt? then return

    Api.item_release(code: code).then(
      (data) =>
        @_receipt.total -= data.price
        @addRow(data.code, data.name, -data.price)

      () =>
        alert("Item not found on receipt: " + code)
        return true
    )

  onPayReceipt: (input) =>
    unless @_receipt? then return
    unless Number.isConvertible(input) then return
    input = input - 0

    if input < @_receipt.total
      alert("Not enough given money!")
      return

    row.addClass("success") for row in [
      @addRow(null, "Subtotal", @_receipt.total, true),
      @addRow(null, "Cash", input),
      @addRow(null, "Return", input - @_receipt.total, true),
    ]

    Api.receipt_finish().then(
      (data) =>
        @_receipt.data = data
        console.log(@_receipt)
        @_receipt = null
        # Mode switching is safe to use again.
        @switcher.setMenuEnabled(true)

      () =>
        alert("Error ending receipt!")
        return true
    )

  onAbortReceipt: =>
    unless @_receipt? then return

    Api.receipt_abort().then(
      (data) =>
        @_receipt.data = data
        console.log(@_receipt)
        @_receipt = null

        @addRow(null, "Aborted", null).addClass("danger")
        # Mode switching is safe to use again.
        @switcher.setMenuEnabled(true)

      () =>
        alert("Error ending receipt!")
        return true
    )

  onLogout: =>
    if @_receipt?
      alert("Cannot logout while receipt is active!")
      return

    Api.clerk_logout().then(
      () =>
        console.log("Logged out #{ @cfg.settings.clerkName }.")
        @cfg.settings.clerkName = null
        @switcher.switchTo(ClerkLoginMode)

      () =>
        alert("Logout failed!")
        return true
    )
