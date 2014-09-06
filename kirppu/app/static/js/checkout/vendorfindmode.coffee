class @VendorFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_find", @)

  constructor: ->
    super
    @vendorList = new VendorList()

  enter: ->
    super
    @cfg.uiRef.body.append(@vendorList.render())

  title: -> "Vendor Search"

  actions: -> [[
    "", (query) =>
      Api.vendor_find(q: query).done(@onVendorsFound)
  ]]

  onVendorsFound: (vendors) =>
    @vendorList.body.empty()
    for vendor, index in vendors
      @vendorList.body.append(@createRow(index + 1, vendor))

  createRow: (index, vendor) =>
    row = $("<tr>")
    row.append($("<td>").text(index))
    for a in ['id', 'name', 'email', 'phone']
      row.append.apply(row, $("<td>").text(vendor[a]))

    switcher = @switcher
    row.click((event) -> switcher.switchTo(vendorReport(vendor)))
