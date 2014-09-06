class @VendorList extends ResultTable
  constructor: ->
    super
    @head.append($('<tr>').append([
      '<th class="receipt_index">#</th>'
      '<th class="receipt_code">id</th>'
      '<th class="receipt_item">name</th>'
      '<th class="receipt_item">email</th>'
      '<th class="receipt_item">phone</th>'
    ].map($)))
