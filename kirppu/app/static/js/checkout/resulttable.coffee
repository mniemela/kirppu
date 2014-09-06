class @ResultTable
  constructor: (caption) ->
    @dom = $('<table class="table table-striped table-hover table-condensed">')
    if caption? then @dom.append($('<caption class="h3">').text(caption))
    @head = $('<tr>')
    @body = $('<tbody>')
    @dom.append($('<thead>').append(@head), @body)

  render: -> @dom
