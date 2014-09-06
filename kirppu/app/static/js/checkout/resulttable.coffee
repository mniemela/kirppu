class @ReceiptTable
  constructor: ->
    @dom = $('<table class="table table-striped table-hover table-condensed">')
    @head = $('<thead>')
    @body = $('<tbody>')
    @dom.append(@head, @body)

  render: -> @dom
