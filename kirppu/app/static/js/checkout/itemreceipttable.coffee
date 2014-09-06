class @ItemReceiptTable extends ResultTable
  constructor: ->
    super
    @head.append([
      '<th class="receipt_index">#</th>'
      '<th class="receipt_code">code</th>'
      '<th class="receipt_item">item</th>'
      '<th class="receipt_price">price</th>'
    ].map($))
