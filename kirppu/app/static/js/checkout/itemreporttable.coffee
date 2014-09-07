class @ItemReportTable extends ItemReceiptTable
  constructor: ->
    super
    @head.append($('<th class="receipt_status">' + gettext('status') + '</th>'))

  update: (items) ->
    @body.empty()
    sum = 0
    for item, index in items
      sum += item.price
      data = [
        index + 1
        item.code
        item.name
        displayPrice(item.price)
        displayState(item.state)
      ]
      row = $('<tr>')
      row.append($('<td>').text(td) for td in data)
      row.data('item', item)
      @body.append(row)

    @body.append($('<tr>').append(
      $('<th colspan="3">').text(gettext('Total') + ':')
      $('<th>').text(displayPrice(sum))
      $('<th>')
    ))
