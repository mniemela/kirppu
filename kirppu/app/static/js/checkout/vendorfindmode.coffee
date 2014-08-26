class @VendorFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_find", @)

  title: -> "Vendor Search"
  subtitle: -> "#{@cfg.settings.clerkName} @ #{@cfg.settings.counterName}"

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
      @cfg.uiRef.receiptResult.append(@createRow(
        index + 1, # In UI, index from one.
        vendor.id,
        vendor.name,
        vendor.email,
        vendor.phone,
      ))

  createRow: (args...) =>
    row = $("<tr>")
    row.append.apply(row, $("<td>").text(a) for a in args)
