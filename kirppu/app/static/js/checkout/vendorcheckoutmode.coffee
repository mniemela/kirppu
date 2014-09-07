class @VendorCheckoutMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_check_out", @)

  constructor: (cfg, switcher, vendor) ->
    super(cfg, switcher)
    @vendorId = if vendor? then vendor.id else null

  enter: ->
    super
    if @vendorId? then do @addVendorInfo

  title: -> "Vendor Check-Out"

  actions: -> [['', @returnItem]]

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
    row = @createRow("", item.code, item.name, item.price)
    @receipt.body.prepend(row)
