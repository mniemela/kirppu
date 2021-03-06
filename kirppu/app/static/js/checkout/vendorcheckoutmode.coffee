class @VendorCheckoutMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_check_out", @)

  constructor: (cfg, switcher, vendor) ->
    super(cfg, switcher)

    @vendorId = if vendor? then vendor.id else null

    @receipt = new ItemReceiptTable('Returned items')
    @lastItem = new ItemReceiptTable()
    @remainingItems = new ItemReceiptTable('Remaining items')

  enter: ->
    super

    @cfg.uiRef.body.prepend(@remainingItems.render())
    @cfg.uiRef.body.prepend(@lastItem.render())
    if @vendorId? then do @addVendorInfo

  glyph: -> "export"
  title: -> "Vendor Check-Out"

  actions: -> [
    ['', @returnItem]
    [@cfg.settings.logoutPrefix,      @onLogout]
  ]

  addVendorInfo: ->
    Api.vendor_get(id: @vendorId).done((vendor) =>
      @cfg.uiRef.body.prepend(
        $('<input type="button">')
          .addClass('btn btn-primary')
          .attr('value', 'Open Report')
          .click(=> @switcher.switchTo(VendorReport, vendor))
      )
      @cfg.uiRef.body.prepend(new VendorInfo(vendor).render())
    )

    Api.item_list(
      vendor: @vendorId
    ).done(@onGotItems)

  onGotItems: (items) =>
    remaining = {BR: 0, ST: 0, MI: 0}
    for item in items when remaining[item.state]?
      row = @createRow("", item.code, item.name, item.price)
      @remainingItems.body.prepend(row)

    returned = {RE: 0, CO: 0}
    for item in items when returned[item.state]?
      row = @createRow("", item.code, item.name, item.price)
      @receipt.body.prepend(row)

  returnItem: (code) =>
    Api.item_find(code: code).done(@onItemFound)

  onItemFound: (item) =>
    if not @vendorId?
      @vendorId = item.vendor
      do @addVendorInfo

    else if @vendorId != item.vendor
      alert('Someone else\'s item!')
      return

    Api.item_checkout(code: item.code).done(@onCheckedOut)

  onCheckedOut: (item) =>
    @receipt.body.prepend($('tr', @lastItem.body))

    @lastItem.body.prepend($('#' + item.code, @remainingItems.body))
