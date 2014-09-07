class @CounterMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("customer_checkout", @)

  constructor: (args..., modeArgs) ->
    super(args...)
    @_receipt = null
    @receiptSum = new ReceiptSum()
    if modeArgs?
      @restoreReceipt(modeArgs)

  title: -> "Checkout"

  actions: -> [
    [@cfg.settings.abortPrefix,       @onAbortReceipt]
    [@cfg.settings.logoutPrefix,      @onLogout]
    [@cfg.settings.payPrefix,         @onPayReceipt]
    [@cfg.settings.removeItemPrefix,  @onRemoveItem]
    ["",                              @onAddItem]
  ]

  enter: ->
    @cfg.uiRef.body.append(@receiptSum.render())
    super
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
    @receipt.body.prepend(row)
    if @_receipt?
      @_setSum(@_receipt.total)
    return row

  onAddItem: (code) =>
    if code.trim() == "" then return

    if not @_receipt?
      @startReceipt(code)
    else
      @reserveItem(code)

  restoreReceipt: (receipt) ->
    @switcher.setMenuEnabled(false)
    Api.receipt_activate(id: receipt.id).then(
      (data) =>
        # RowCount is set to zero, as addRow will increase this.
        @_receipt =
          rowCount: 0
          total: data.total
          data: data
        @receipt.body.empty()
        for item in data.items
          price = if item.action == "DEL" then -item.price else item.price
          @addRow(item.code, item.name, price)
        @_setSum(@_receipt.total)

      () =>
        alert("Could not restore receipt!")
        @switcher.setMenuEnabled(true)
    )

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
        @receipt.body.empty()
        @_setSum()
        @reserveItem(code)

      (jqHXR) =>
        alert("Could not start receipt!")
        # Rollback.
        @_receipt = null
        @switcher.setMenuEnabled(true)
        return true
    )

  _setSum: (sum=0, ret=null) ->
    text = "Total: " + (sum).formatCents() + " €"
    if ret?
      text += " / Return: " + (ret).formatCents() + " €"
    @receiptSum.set(text)
    @receiptSum.setEnabled(@_receipt?)

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

    if input > 400*100
      alert("Not accepting THAT much money!")
      return

    return_amount = input - @_receipt.total
    row.addClass("success") for row in [
      @addRow(null, "Subtotal", @_receipt.total, true),
      @addRow(null, "Cash", input),
      @addRow(null, "Return", return_amount, true),
    ]

    # Also display the return amount in the top.
    @_setSum(@_receipt.total, return_amount.round5())

    Api.receipt_finish().then(
      (data) =>
        @_receipt.data = data
        console.log(@_receipt)
        @_receipt = null
        # Mode switching is safe to use again.
        @switcher.setMenuEnabled(true)
        @receiptSum.setEnabled(false)

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
        @receiptSum.setEnabled(false)

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
