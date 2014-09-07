class @VendorCheckoutMode extends ItemCheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_check_out", @)

  constructor: ->
    super
    @vendorId = null

  title: -> "Vendor Check-Out"

  actions: -> [['', @returnItem]]

  addVendorInfo: ->
    @cfg.uiRef.body.prepend(VendorInfo.byId(@vendorId).render())

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
