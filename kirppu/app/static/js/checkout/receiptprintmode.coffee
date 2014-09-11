class @ReceiptPrintMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("reports", @)

  @strTotal: "Total"
  @strTitle: "Find receipt"
  @strSell: "%d, served by %c"

  constructor: () ->
    super
    @receipt = new PrintReceiptTable()

  enter: ->
    super
    @cfg.uiRef.body.append(@receipt.render())

  glyph: -> "list-alt"
  title: -> @constructor.strTitle
  subtitle: -> ""

  actions: -> [
    ["", @findReceipt],
  ]

  findReceipt: (code) =>
    Api.receipt_get(item: code).then(
      (data) =>
        @renderReceipt(data)
      () =>
        alert("Item not found in receipt!")
    )

  renderReceipt: (receiptData) ->
    @receipt.body.empty()
    for item in receiptData.items
      if item.action != "ADD"
        continue
      row = PrintReceiptTable.createRow(item.vendor, item.code, item.name, item.price, false)
      @receipt.body.append(row)

    replacer = (s) ->
      switch s[1]
        when 'd' then DateTimeFormatter.datetime(receiptData.sell_time)
        when 'c' then receiptData.clerk.print
        else s[1]

    sellFmt = /%[dc%]/g
    sellStr = @constructor.strSell.replace(sellFmt, replacer)

    @receipt.body.append(row) for row in [
      @constructor.middleLine
      PrintReceiptTable.createRow("", "", @constructor.strTotal, receiptData.total, true)
      PrintReceiptTable.joinedLine(sellStr)
    ].concat(@constructor.tailLines)

  @middleLine: PrintReceiptTable.joinedLine()
  @tailLines: [
    PrintReceiptTable.joinedLine()
  ]
