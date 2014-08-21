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

  actions: -> [["", @onVendorSearch]]

  onVendorSearch: (query) =>
    (
      # Heuristics to select what to search.
      if query.trim() == ""
        (->)
      else if query.match(/^[0-9\s]+$/)?
        @findPhoneNumber
      else if query.match(/^#[0-9]+$/)?
        @findId
      else if query.match(/@/)?
        @findEmail
      else
        @findName
    )(query)

  findId: (query) =>
    # Remove leading hash.
    query = query.replace(/#/, '')
    Api.findVendors(id: query, @onVendorsFound)

  findName: (query) =>
    Api.findVendors(name: query, @onVendorsFound)

  findPhoneNumber: (query) =>
    # Remove all whitespace.
    query = query.replace(/\s/g, '')
    Api.findVendors(phone: query, @onVendorsFound)

  findEmail: (query) =>
    Api.findVendors(email: query, @onVendorsFound)

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
