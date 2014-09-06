class @VendorFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_find", @)

  title: -> "Vendor Search"

  columns: -> [
    '<th class="receipt_index">#</th>',
    '<th class="receipt_code">id</th>',
    '<th class="receipt_item">name</th>',
    '<th class="receipt_item">email</th>',
    '<th class="receipt_item">phone</th>',
  ].map($)

  actions: -> [[
    "", (query) =>
      Api.vendor_find(q: query).done(@onVendorsFound)
  ]]

  onVendorsFound: (vendors) =>
    @clearReceipt()
    for vendor, index in vendors
      @cfg.uiRef.receiptResult.append(@createRow(index + 1, vendor))

  createRow: (index, vendor) =>
    row = $("<tr>")
    row.append($("<td>").text(index))
    for a in ['id', 'name', 'email', 'phone']
      row.append.apply(row, $("<td>").text(vendor[a]))

    switcher = @switcher
    row.click((event) -> switcher.switchTo(vendorReport(vendor)))
