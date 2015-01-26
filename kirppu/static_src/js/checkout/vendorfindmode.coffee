class @VendorFindMode extends CheckoutMode
  ModeSwitcher.registerEntryPoint("vendor_find", @)

  constructor: (args..., query) ->
    super
    @vendorList = new VendorList()
    @query = query

  enter: ->
    super
    @cfg.uiRef.body.append(@vendorList.render())

    if @query?
      Api.vendor_find(q: @query).done(@onVendorsFound)

  glyph: -> "user"
  title: -> "Vendor Search"
  inputPlaceholder: -> "Search"

  actions: -> [
    ["", (query) => Api.vendor_find(q: query).done(@onVendorsFound)]
    [@cfg.settings.logoutPrefix,      @onLogout]
  ]

  onVendorsFound: (vendors) =>
    @vendorList.body.empty()
    for vendor_, index_ in vendors
      ((vendor, index) =>
        @vendorList.append(
          vendor,
          index + 1,
          (=> @switcher.switchTo(VendorReport, vendor)),
        )
      )(vendor_, index_)

