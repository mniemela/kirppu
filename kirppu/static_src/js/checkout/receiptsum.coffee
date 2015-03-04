class @ReceiptSum
  constructor: ->
    @dom = $('<p class="lead text-right">')

  render: -> @dom

  set: (sum) -> @dom.text(sum)

  setEnabled: (enabled=true) -> setClass(@dom, "text-muted", not enabled)
