class @VendorInfo
  constructor: (vendor) ->
    @dom = $('<div class="vendor-info-box">')
    @dom.append($('<h3>').text('Vendor'))

    if vendor?
      @_setInfo(vendor)

  _setInfo: (vendor) =>
    list = $('<dl class="dl-horizontal">')
    for attr in ['id', 'name', 'email', 'phone']
      list.append($('<dt>').text(attr))
      list.append($('<dd>').text(vendor[attr]))
    @dom.append(list)

  render: -> @dom

  @byId: (id) ->
    v = new VendorInfo(null)
    Api.vendor_get(id: id).done(v._setInfo)
    return v
