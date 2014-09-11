class @VendorList extends ResultTable
  constructor: ->
    super
    @head.append([
      '<th class="receipt_index">#</th>'
      '<th class="receipt_username">username</th>'
      '<th class="receipt_vendor_id">id</th>'
      '<th class="receipt_name">name</th>'
      '<th class="receipt_email">email</th>'
      '<th class="receipt_phone">phone</th>'
    ].map($))

  append: (vendor, index, action) ->
    row = $("<tr>")
    row.addClass('receipt_tr_clickable')
    row.append($("<td>").text(index))
    row.append(
      for a in ['username', 'id', 'name', 'email', 'phone']
        $("<td>").text(vendor[a])
    )
    row.click(action)
    @body.append(row)
