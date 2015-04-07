class @ItemFindList extends ResultTable
  constructor: ->
    super
    @head.append([
      '<th class="receipt_index">#</th>'
      '<th class="receipt_code">' + gettext('code') + '</th>'
      '<th class="receipt_item">' + gettext('item') + '</th>'
      '<th class="receipt_price">' + gettext('price') + '</th>'
      '<th class="receipt_type">' + gettext('type') + '</th>'
      '<th class="receipt_name">' + gettext('vendor') + '</th>'
      '<th class="receipt_status">' + gettext('status') + '</th>'
    ].map($))

  append: (item, index) ->
    row = $("<tr>")
    row.append([
      $("<td>").text(index)
      $("<td>").text(item.code)
      $("<td>").text(item.name)
      $("<td>").text(displayPrice(item.price))
      $("<td>").text(item.itemtype)
      $("<td>").text(item.vendor.name)
      $("<td>").text(item.state)
    ])
    @body.append(row)
