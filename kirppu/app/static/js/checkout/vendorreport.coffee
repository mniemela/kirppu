states =
  compensable:
    SO: 'sold'

  returnable:
    BR: 'on display'
    ST: 'about to be sold'

  other:
    MI: 'missing'
    RE: 'returned to the vendor'
    CO: 'sold and compensated to the vendor'
    AD: 'not brought to the event'

tables = [
  [states.compensable,'Compensable Items']
  [states.returnable, 'Returnable Items']
  [states.other,      'Other Items']
]

# Create a new class for the report mode of the vendor.
@vendorReport = (vendor) ->
  class VendorReport extends CheckoutMode

    title: -> "Item Report"

    enter: ->
      super
      Api.item_list(
        vendor: vendor.id
      ).done(@onGotItems)

    onGotItems: (items) =>
      for [states, name] in tables
        table = new ItemReportTable(name)
        @listItems(items, table, states)
        if table.body.children().length > 0
          @cfg.uiRef.body.append(table.render())

    listItems: (items, table, states) ->
      sum = 0
      for i in items when states[i.state]?
        sum += i.price
        table.append(i.code, i.name, displayPrice(i.price), states[i.state])
      if sum > 0
        table.total(displayPrice(sum))
