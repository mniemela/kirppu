class @VendorInfo
  constructor: (vendor) ->
    @dom = $('<div class="vendor-info-box">')
    @dom.append($('<h3>').text(gettext('Vendor')))

    list = $('<dl class="dl-horizontal">')
    for attr in ['name', 'email', 'phone', 'id']
      list.append($('<dt>').text(attr))
      list.append($('<dd>').text(vendor[attr]))
    @dom.append(list)

  render: -> @dom
