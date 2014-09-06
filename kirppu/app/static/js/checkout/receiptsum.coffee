class @ReceiptSum
  constructor: ->
    @dom = $('<p class="lead text-right">')

  render: -> @dom

  set: (sum) -> @dom.text(sum)
