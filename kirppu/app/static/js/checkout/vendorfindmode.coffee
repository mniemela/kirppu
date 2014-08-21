class @VendorFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_find", @)

  constructor: (args...) ->
    super(args...)
    @_dummy =
      id: "42"
      name: "Erkki Esimerkki"
      email: "erkki@example.org"
      phone: "0123456789"

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
    # TODO: actual ajax search
    @onVendorsFound(@_findBy('id', query))

  findPhoneNumber: (query) =>
    # Remove all whitespace.
    query = query.replace(/\s/g, '')
    # TODO: actual ajax search
    @onVendorsFound(@_findBy('phone', query))

  findEmail: (query) =>
    # TODO: actual ajax search
    @onVendorsFound(@_findBy('email', query))

  findName: (query) =>
    # TODO: actual search from backend
    @onVendorsFound(@_findBy('name', query))

  _findBy: (property, query) =>
    if @_dummy[property].indexOf(query) >= 0 then [@_dummy] else []

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
